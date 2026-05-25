function fastArrayModeling(mws, unitParams, codingMatrix, layerDistance)
% FASTARRAYMODELING 高速阵列建模 (基于样板复制)
% 适用规模：数千单元级别
% -------------------------------------------------------------------------

% --- 1. 数据格式标准化 (兼容 Cell 和 矩阵) ---
if ~iscell(codingMatrix)
    temp = codingMatrix; codingMatrix = cell(1,1); codingMatrix{1} = temp;
elseif iscell(codingMatrix) && isscalar(codingMatrix{1})
    try temp = cell2mat(codingMatrix); codingMatrix = cell(1,1); codingMatrix{1} = temp; catch, end
end

codeLayer = length(codingMatrix);
[rows, cols] = size(codingMatrix{1});

% 计算坐标网格
dx = unitParams.unitSize(1);
dy = unitParams.unitSize(2);
dz = unitParams.unitSize(3);

x_vec = ((1:cols) - 0.5) * dx - (cols * dx) / 2;
y_vec = ((1:rows) - 0.5) * dy - (rows * dy) / 2;
[X_map, Y_map] = meshgrid(x_vec, y_vec);

% 拉直数据
list_centers = reshape(cat(3, X_map, Y_map, zeros(size(X_map))), [], 3);
list_codes = cell(codeLayer, 1);
for i = 1:codeLayer
    list_codes{i} = codingMatrix{i}(:);
end

% -------------------------------------------------------------------------
% 2. 核心加速：建立样板 (Template)
% -------------------------------------------------------------------------
fprintf('=== 正在构建样板单元 (Code 1 - %d) ===\n', unitParams.codeNum);

% 确保在原点
activateWCS(mws, [0 0 1], [0 0 0], [1 0 0], 1);

for c = 1 : unitParams.codeNum
    tplName = sprintf('Template_%d', c);
    
    % 调用您的建模函数，在原点建立样板
    % 注意：这里直接传 [0,0,0] 作为中心
    unitParams.codeModeling(mws, c, [0, 0, 0], tplName);
    
    % (可选) 将样板设为不可见，提高绘图性能
    % mws.invoke('AddToHistory', ['hide ' tplName], ['Component.WaitVisibility "' tplName '", "False"']);
end

disp('>>> 样板构建完成，开始阵列复制...');

% -------------------------------------------------------------------------
% 3. 阵列复制循环
% -------------------------------------------------------------------------
SetOriginZ = 0; % Z轴起始点

% 暂停屏幕刷新以加速 (如果MatCST支持)
try mws.invoke('ScreenUpdating', 'False'); catch, end 

total_units = rows * cols * codeLayer;
counter = 0;
tic;

for j = 1:codeLayer
    fprintf('正在生成第 %d / %d 层...\n', j, codeLayer);
    current_codes = list_codes{j};
    
    for i = 1 : (rows * cols)
        this_code = current_codes(i);
        if this_code == 0, continue; end % 跳过0编码
        
        % 目标绝对坐标
        tx = list_centers(i, 1);
        ty = list_centers(i, 2);
        tz = list_centers(i, 3) + SetOriginZ;
        
        % 源样板名称
        srcName = sprintf('Template_%d', this_code);
        
        % 新单元名称 (例如 L1_U23_C2)
        dstName = sprintf('L%d_U%d_C%d', j, i, this_code);
        
        % --- 调用辅助函数执行复制 ---
        % 注意：因为样板在(0,0,0)，所以平移向量就是目标坐标 [tx, ty, tz]
        translationObj(mws, srcName, tx, ty, tz, 1, 1, dstName);
        
        % 进度条
        counter = counter + 1;
        if mod(counter, 100) == 0
            time_per_100 = toc;
            fprintf('  已完成: %d / %d (%.2f s/100个)\n', counter, total_units, time_per_100);
            tic;
        end
    end
    
    % 更新层间距
    if j < codeLayer
        distIdx = min(j, length(layerDistance));
        SetOriginZ = SetOriginZ + layerDistance(distIdx) + dz;
    end
end

% -------------------------------------------------------------------------
% 4. 收尾工作
% -------------------------------------------------------------------------
% 恢复屏幕刷新
try mws.invoke('ScreenUpdating', 'True'); catch, end 
activateWCS(mws, [0 0 1], [0 0 0], [1 0 0], 0);

% 询问是否删除样板
button = questdlg('建模完成！是否删除原始样板(Template_1...)?', ...
    '完成', '删除样板', '保留', '删除样板');
if strcmp(button, '删除样板')
    for c = 1:unitParams.codeNum
        deleteComponent(mws, sprintf('Template_%d', c));
    end
end

disp('=== 所有任务完成 ===');

end