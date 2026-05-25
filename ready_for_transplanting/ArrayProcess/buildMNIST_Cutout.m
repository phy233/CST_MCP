function buildMNIST_Cutout(mws, imgMatrix, pixelSize, thickness, plateName)
% BUILDMNIST_CUTOUT 在CST中建立镂空数字金属板
% 输入:
%   mws: CST对象
%   imgMatrix: 28x28 的二维矩阵 (值域 0~1 或 0~255)
%   pixelSize: 单个像素对应的物理尺寸 (mm)，例如 0.5
%   thickness: 金属板厚度 (mm)
%   plateName: 金属板的名称 (需已存在，或由本函数创建)

% -------------------------------------------------------------------------
% 1. 预处理数据
% -------------------------------------------------------------------------
% 确保是二值化图像 (阈值设为 0.5)
if max(imgMatrix(:)) > 1
    imgMatrix = double(imgMatrix) / 255.0;
end
binaryImg = imgMatrix > 0.5;

% 获取图像尺寸 (通常是 28x28)
[rows, cols] = size(binaryImg);

% 计算总尺寸
totalWidth_X = cols * pixelSize;
totalHeight_Y = rows * pixelSize;

% -------------------------------------------------------------------------
% 2. 创建底板 (如果底板还不存在)
% -------------------------------------------------------------------------
% 尝试选中底板，如果报错说明不存在，则创建
% 这里为了简单，假设如果没有底板，就新建一个刚好包围数字的板
try 
    % 检查是否存在 (利用CST Select命令测试)
    % 这里简单起见，我们直接画一个新的覆盖板，名字叫 plateName
    % 中心定位在 (0,0)
    
    % 定义底板材料 (假设是 PEC)
    if ~check_material_exists(mws, 'PEC')
        % 如果没有PEC定义，通常默认就有，这里略过或调用 defineMaterial
    end
    
    % 画一个稍大一点的板 (边框留白 2个像素)
    margin = 2 * pixelSize; 
    
    % 底板坐标范围
    x_min = -totalWidth_X/2 - margin;
    x_max = totalWidth_X/2 + margin;
    y_min = -totalHeight_Y/2 - margin;
    y_max = totalHeight_Y/2 + margin;
    
    % 调用您的 defineBrick
    % 注意：defineBrick(mws, name, component, center, a, b, h, material)
    % 您之前的 defineBrick 是中心定义法，这里我们转换一下坐标
    center = [0, 0, 0];
    w_plate = (x_max - x_min);
    h_plate = (y_max - y_min);
    
    defineBrick(mws, plateName, 'TempDigits', center, w_plate, h_plate, thickness, 'PEC');
    
catch
    disp('底板创建可能遇到问题，或者已存在');
end

% -------------------------------------------------------------------------
% 3. 构建数字实体 (Voxelization)
% -------------------------------------------------------------------------
digitObjName = 'Digit_Tool_Body';
isFirstPixel = true;

% 关闭屏幕刷新加速
mws.invoke('ScreenUpdating', 'False');

% 计算起始坐标 (左上角)
x0 = -totalWidth_X / 2;
y0 = totalHeight_Y / 2; % 图像通常Y向下，但CST里Y向上，需要注意翻转

for r = 1:rows
    for c = 1:cols
        % 如果该像素是黑色的 (有笔画)
        if binaryImg(r, c)
            
            % 计算该像素小方块的中心坐标
            % r对应Y (注意图像坐标系转换), c对应X
            % 图像第1行是Y的最大值
            px = x0 + (c - 0.5) * pixelSize;
            py = y0 - (r - 0.5) * pixelSize;
            
            thisPixelName = sprintf('px_%d_%d', r, c);
            
            % 画小方块
            center_pixel = [px, py, 0];
            defineBrick(mws, thisPixelName, 'TempDigits', center_pixel, pixelSize, pixelSize, thickness, 'Vacuum');
            
            if isFirstPixel
                % 第一个像素，直接改名为总物体名
                renameObj(mws, 'Solid', sprintf('TempDigits:%s', thisPixelName), digitObjName);
                isFirstPixel = false;
            else
                % 后续像素，画出来后立刻与第一个像素合并 (Boolean Add)
                % 注意：您需要确保有 addObj.m (Boolean Add)
                % 假设您的 addObj 是: addObj(mws, component, baseObj, component, toolObj)
                
                % 这里需要一点技巧：CST里合并后，物体名通常保留第一个
                addObj(mws, 'TempDigits', digitObjName, 'TempDigits', thisPixelName);
            end
        end
    end
end

% -------------------------------------------------------------------------
% 4. 执行镂空 (Boolean Subtract)
% -------------------------------------------------------------------------
% Component1:plateName  MINUS  TempDigits:Digit_Tool_Body

% 确保您的 subtractObj.m 可以在不同 Component 间操作
% 如果不行，可能需要先 moveComponent
% 这里假设 substractObj(mws, baseComp, baseName, toolComp, toolName)
% 或者您提供的 substractObj 只有名字参数

try
    % 调用布尔减
    % 假设参数是: (mws, baseObjName, toolObjName) 
    % 您需要根据您的 substractObj.m 实际参数调整
    substractObj(mws, 'TempDigits',plateName, 'TempDigits',digitObjName);
catch ME
    warning(ME.identifier,'布尔减操作失败，请手动检查: %s', ME.message);
end

% 恢复屏幕
mws.invoke('ScreenUpdating', 'True');

end

% --- 辅助内部函数：重命名 (防止之前的 renameObj 没定义) ---
function renameObj(mws, type, oldName, newName)
    cmd = sprintf('With %s\n.Rename "%s", "%s"\nEnd With', type, oldName, newName);
    mws.invoke('AddToHistory', 'Rename', cmd);
end