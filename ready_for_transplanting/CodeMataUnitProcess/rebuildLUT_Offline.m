close all; clear; clc;

%% --- 1. 设置部分 (请根据你之前的运行情况修改) ---

% 1.1 数据源文件夹 (之前保存 S_Parameters txt 的那个文件夹)
% 请修改为你实际的路径
sourceDataDir = 'E:\seu\UnitOptimizing\Cross\Task_UnitOptimize_20251217_112302\S_Parameters';

% 1.2 想要提取的新频率
newTargetFreq = 7.0; % 修改这里！比如改成 10GHz

% 1.3 参数扫描范围 (必须与之前仿真时完全一致！)
scanParameter = {'lx', 'ly1'};
scanRange = {3:0.4:10.5, 3:0.4:10.5};

%% --- 2. 初始化新 LUT ---
fprintf('========================================\n');
fprintf('开始离线重构 LUT (Target Freq = %.2f GHz)\n', newTargetFreq);
fprintf('数据源: %s\n', sourceDataDir);
fprintf('========================================\n');

% 初始化空表
newLUT = table([], [], [], [], [], [], ...
    'VariableNames', {'lx', 'ly1', 'mag_Y', 'arg_Y', 'mag_x', 'arg_X'});

total_steps = length(scanRange{1}) * length(scanRange{2});
current_step = 0;

%% --- 3. 离线循环处理 ---

for i = 1:length(scanRange{1})
    val_1 = scanRange{1}(i);
    name_1 = scanParameter{1};
    
    for j = 1:length(scanRange{2})
        current_step = current_step + 1;
        val_2 = scanRange{2}(j);
        name_2 = scanParameter{2};
        
        if mod(current_step, 100) == 0
            fprintf('进度: %d / %d ...\n', current_step, total_steps);
        end
        
        try
            % 3.1 构造文件名 (必须与保存时的命名规则一致)
            % 注意：你之前的命名里有 SZmax(1) 变成了 SZmax_1_ 等替换逻辑
            
            % --- 读取 Y 极化 (Mode 1) ---
            file_Y = constructFileName('SZmax(1),Zmax(1)', name_1, val_1, name_2, val_2);
            fullPath_Y = fullfile(sourceDataDir, file_Y);
            
            [freq, S_Re, S_Im] = robustReadSParam(fullPath_Y); % 使用智能读取函数
            [mag_y, arg_y] = getInterpData(freq, S_Re, S_Im, newTargetFreq);
            
            % --- 读取 X 极化 (Mode 2) ---
            file_X = constructFileName('SZmax(2),Zmax(2)', name_2, val_1, name_2, val_2); % 注意: 这里文件名构造可能需要微调
            % 修正：上面的 file_X 构造可能有些问题，根据你之前的代码，
            % Mode 2 应该是 SZmax(2), 但参数还是 lx, ly1
            file_X = constructFileName('SZmax(2),Zmax(2)', name_1, val_1, name_2, val_2);
            fullPath_X = fullfile(sourceDataDir, file_X);
            
            [freq, S_Re, S_Im] = robustReadSParam(fullPath_X);
            [mag_x, arg_x] = getInterpData(freq, S_Re, S_Im, newTargetFreq);
            
            % 3.2 存入新表
            newRow = {val_1, val_2, mag_y, arg_y, mag_x, arg_x};
            newLUT = [newLUT; newRow];
            
        catch ME
            fprintf('警告: 无法读取参数 %s=%.2f, %s=%.2f 的文件。\n原因: %s\n', ...
                name_1, val_1, name_2, val_2, ME.message);
            % 可以选择填入 NaN 占位
            newLUT = [newLUT; {val_1, val_2, NaN, NaN, NaN, NaN}];
        end
    end
end

%% --- 4. 保存结果 ---
timeStamp = datestr(now, 'yyyymmdd_HHMMSS');
saveName = sprintf('Rebuilt_LUT_Freq_%.2f_%s.txt', newTargetFreq, timeStamp);
savedir = ['E:\seu\UnitOptimizing\Cross\Task_UnitOptimize_20251217_112302\',saveName];
writetable(newLUT, savedir, 'Delimiter', '\t');
fprintf('\n重构完成！新 LUT 已保存为: %s\n', saveName);


%% === 辅助函数部分 ===

function fName = constructFileName(resName, p1N, p1V, p2N, p2V)
    % 复刻你之前保存文件的命名逻辑
    safeResName = replace(resName, {',', '(', ')'}, '_');
    % 格式: S_SZmax_1__Zmax_1__lx_2.00_ly1_2.00.txt
    fName = sprintf('S_%s_%s_%.2f_%s_%.2f.txt', ...
                    safeResName, p1N, p1V, p2N, p2V);
end

function [mag, phase] = getInterpData(f, re, im, targetF)
    % 简单的插值封装
    re_i = interp1(f, re, targetF, 'linear');
    im_i = interp1(f, im, targetF, 'linear');
    c = complex(re_i, im_i);
    mag = abs(c);
    phase = rad2deg(angle(c));
end

function [freq, re, im] = robustReadSParam(filePath)
    % --- 智能读取函数：兼容“乱码宽表”和“标准长表” ---
    if ~exist(filePath, 'file')
        error('文件不存在: %s', filePath);
    end
    
    T = readtable(filePath);
    raw = table2array(T);
    
    [rows, cols] = size(raw);
    
    if rows > 10 && cols == 3
        % 情况 A: 标准格式 (N行3列) -> 直接读
        freq = raw(:, 1);
        re   = raw(:, 2);
        im   = raw(:, 3);
    elseif rows == 1 && cols > 10
        % 情况 B: 乱码宽格式 (1行 3N 列) -> 需要重组
        % 假设顺序是: Freq全集, Re全集, Im全集 (这是 writetable 拆分数组的默认行为)
        numPoints = cols / 3;
        
        % 强制检查是否为整数
        if mod(numPoints, 1) ~= 0
            error('数据列数(%d)不是3的倍数，无法解析', cols);
        end
        
        freq = raw(1, 1:numPoints)';
        re   = raw(1, numPoints+1 : 2*numPoints)';
        im   = raw(1, 2*numPoints+1 : end)';
    else
        error('无法识别的文件数据格式: %d 行 %d 列', rows, cols);
    end
end