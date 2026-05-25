close all;
clear;
clc;

%% --- 0. 初始化与路径配置 ---

% 1. 定义结果根目录
rootResultDir = 'E:\seu\UnitOptimizing\Cross';

% 2. 生成带时间戳的任务文件夹名
current_time = now;
timeStampStr = datestr(current_time, 'yyyymmdd_HHMMSS');
taskFolderName = ['Task_UnitOptimize_', timeStampStr];
fullSavePath = fullfile(rootResultDir, taskFolderName);

% 3. 创建主任务文件夹
if ~exist(fullSavePath, 'dir')
    [status, msg] = mkdir(fullSavePath);
    if ~status
        error('无法创建文件夹: %s\n错误信息: %s', fullSavePath, msg);
    end
end

% 4. (可选) 创建一个子文件夹专门放S参数txt，防止主文件夹文件数爆炸
sParamDir = fullfile(fullSavePath, 'S_Parameters');
mkdir(sParamDir);

% 5. 开启 Diary 日志 (黑匣子)
% 放在主文件夹下，记录所有屏幕输出
logFile = fullfile(fullSavePath, 'simulation_process.log');
diary(logFile);
diary on;

fprintf('========================================\n');
fprintf('任务开始：十字形编码单元参数扫描\n');
fprintf('结果存储路径: %s\n', fullSavePath);
fprintf('========================================\n');


%% 仿真前工程文件准备

% 链接工程文件
proj_addr = 'E:\seu\10.1002adom.202001609\newunit_reflect.cst';
mws = initializeCSTproj(proj_addr);

if isempty(mws)
    error('无法唤起CST，任务终止');
end

fprintf('已连接到工程文件%s\n',proj_addr);

% 获取参数
parameterList = getParameterList(mws);
disp('当前参数：');
for idx = 1:numel(parameterList)
    disp(parameterList{idx});
end

%设定扫描的参数
scanParameter = {'lx','ly1'};
scanRange = {3:0.4:10.5, 3:0.4:10.5};
targetFreq = 8;

% 初始化LUT
codeLUT = table([], [], [], [], [], [], ...
    'VariableNames', {'lx', 'ly1', 'mag_Y', 'arg_Y', 'mag_x', 'arg_X'});

%% 开始扫参
fprintf('\n=== 开始参数扫描 ===\n');
fprintf('目标频率: %.2f GHz\n', targetFreq);

total_steps = length(scanRange{1}) * length(scanRange{2});
current_step = 0;

for paraIdx_1 = 1:numel(scanRange{1})

    % 获取要扫描的第一个参数
    currentParaName_1 = scanParameter{1};
    currentParaVal_1 = scanRange{1}(paraIdx_1);

    for paraIdx_2 = 1:numel(scanRange{2})

        %获取要扫描的第二个参数
        currentParaName_2 = scanParameter{2};
        currentParaVal_2 = scanRange{2}(paraIdx_2);

        current_step = current_step + 1;
        fprintf('\n[进度 %d/%d] 设置参数 -> %s: %.4f, %s: %.4f\n', ...
            current_step, total_steps, currentParaName_1,currentParaVal_1,currentParaName_2,currentParaVal_2);

        try
            % 参数检查
            if ~(ensureParameterExist(mws,currentParaName_1)&&ensureParameterExist(mws,currentParaName_2))
                error('当前参数不存在：%s,%s',currentParaName_1,currentParaVal_1);
            end


            % 删除已有结果并更新结构
            deleteResult(mws);
            if ~updateStructure(mws,0)
                error('结构更新失败，当前参数：%s,%s',currentParaName_1,currentParaVal_1)
            end

            % 修改参数值
            settingParameter(mws,currentParaName_1,currentParaVal_1);
            settingParameter(mws,currentParaName_2,currentParaVal_2);

            % 运行仿真
            startCurrentSolver(mws);

            %             %获取模式1的S11
            %             [freq, S_Re, S_Im] = smartReadSParameter(mws,'SZmax(1),Zmax(1)');
            %             [S_Mag, S_Phase, S_Re, S_Im] = getSParamAtFreq(freq, S_Re, S_Im, targetFreq);
            %             fprintf('SZmax(1),Zmax(1)在%.4f下幅值和相位分别为：%.4f,%.4f',targetFreq,S_Mag, S_Phase);
            %
            %             mag_y = S_Mag;
            %             arg_y = S_Phase;
            %
            %             % 保存S11
            %             % 1. 准备原始名称和时间戳
            %             rawName = 'SZmax(1),Zmax(1)';
            %             timeStamp = datestr(now, 'yyyymmdd_HHMMSS');
            %
            %             % 2. 文件名清洗 (Best Practice)
            %             % 逗号和括号在文件名中虽然合法但不推荐，建议替换为下划线
            %             % 替换后变成: SZmax_1__Zmax_1__时间戳.txt
            %             safeName = replace(rawName, {',', '(', ')'}, '_');
            %
            %             % 3. 构造完整文件名
            %             % 最终文件名示例: SZmax_1__Zmax_1__20231027_153022.txt
            %             fileName = sprintf('%s_%s.txt', safeName, timeStamp);
            %
            %             % 4. 整合数据为 Table (推荐方式)
            %             % 将频率、实部、虚部整合在一起，方便查看和后续读取
            %             saveData = table(freq, S_Re, S_Im, ...
            %                 'VariableNames', {'Frequency_GHz', 'Real_Part', 'Imaginary_Part'});
            %
            %             % 5. 保存文件
            %             writetable(saveData, fileName, 'Delimiter', '\t'); % 使用制表符分隔，txt可读性好
            %             fprintf('数据已成功保存至文件: %s\n', fileName);
            %
            %             % 获取模式2的S11
            %             [freq, S_Re, S_Im] = smartReadSParameter(mws,'SZmax(2),Zmax(2)');
            %             [S_Mag, S_Phase, S_Re, S_Im] = getSParamAtFreq(freq, S_Re, S_Im, targetFreq);
            %             fprintf('SZmax(1),Zmax(1)在%.4f下幅值和相位分别为：%.4f,%.4f',targetFreq,S_Mag, S_Phase);
            %
            %             mag_x = S_Mag;
            %             arg_x = S_Phase;
            %
            %             % 保存S11
            %             % 1. 准备原始名称和时间戳
            %             rawName = 'SZmax(2),Zmax(2)';
            %             timeStamp = datestr(now, 'yyyymmdd_HHMMSS');
            %
            %             % 2. 文件名清洗 (Best Practice)
            %             % 逗号和括号在文件名中虽然合法但不推荐，建议替换为下划线
            %             % 替换后变成: SZmax_1__Zmax_1__时间戳.txt
            %             safeName = replace(rawName, {',', '(', ')'}, '_');
            %
            %             % 3. 构造完整文件名
            %             % 最终文件名示例: SZmax_1__Zmax_1__20231027_153022.txt
            %             fileName = sprintf('%s_%s.txt', safeName, timeStamp);
            %
            %             % 4. 整合数据为 Table (推荐方式)
            %             % 将频率、实部、虚部整合在一起，方便查看和后续读取
            %             saveData = table(freq, S_Re, S_Im, ...
            %                 'VariableNames', {'Frequency_GHz', 'Real_Part', 'Imaginary_Part'});
            %
            %             % 5. 保存文件
            %             writetable(saveData, fileName, 'Delimiter', '\t'); % 使用制表符分隔，txt可读性好
            %             fprintf('数据已成功保存至文件: %s\n', fileName);
            %
            %
            %             % 数据拼接填入LUT
            %             newRow = [currentParaVal_1, currentParaVal_2, mag_y, arg_y, mag_x, arg_x];
            %             codeLUT = [codeLUT; newRow];

            % 3. 处理结果 (提取 + 保存)
            % 定义一个结构体暂存本次循环的数据，方便后面填表
            resStruct = struct('mag_y', 0, 'arg_y', 0, 'mag_x', 0, 'arg_x', 0);

            % --- 处理 Mode 1 (Y极化) ---
            targetResName = 'SZmax(1),Zmax(1)';
            [freq, S_Re, S_Im] = smartReadSParameter(mws, targetResName);

            % 修正：确保 getSParamAtFreq 函数支持向量输入
            [S_Mag, S_Phase, ~,~] = getSParamAtFreq(freq, S_Re, S_Im, targetFreq);

            resStruct.mag_y = S_Mag;
            resStruct.arg_y = S_Phase;

            % 保存 Mode 1 曲线到文件
            saveSParamToFile(freq, S_Re, S_Im, sParamDir, targetResName, currentParaName_1,currentParaVal_1,currentParaName_2,currentParaVal_2);

            % --- 处理 Mode 2 (X极化) ---
            targetResName = 'SZmax(2),Zmax(2)';
            [freq, S_Re, S_Im] = smartReadSParameter(mws, targetResName);
            [S_Mag, S_Phase, ~,~] = getSParamAtFreq(freq, S_Re, S_Im, targetFreq);

            resStruct.mag_x = S_Mag;
            resStruct.arg_x = S_Phase;

            % 保存 Mode 2 曲线到文件
            saveSParamToFile(freq, S_Re, S_Im, sParamDir, targetResName, currentParaName_1,currentParaVal_1,currentParaName_2,currentParaVal_2);

            % 4. 数据写入 LUT (修正拼接逻辑)
            % 使用 cell 数组构建一行，然后转为 table 拼接到主表
            newRow = {currentParaVal_1, currentParaVal_2, resStruct.mag_y, resStruct.arg_y, resStruct.mag_x, resStruct.arg_x};
            codeLUT = [codeLUT; newRow];

            fprintf('    -> 结果提取成功: MagX=%.3f, ArgX=%.2f | MagY=%.3f, ArgY=%.2f\n', ...
                resStruct.mag_x, resStruct.arg_x, resStruct.mag_y, resStruct.arg_y);

        catch ME
            warning('当前扫描参数：%s:%.4f;%s:%.4f仿真失败',currentParaName_1,currentParaVal_1,currentParaName_2,currentParaVal_2');
            fprintf('错误：%s\n',ME.message);
        end
    end
end

%% --- 3. 最终 LUT 保存 ---

% 保持在同一个任务文件夹下
lutTxtPath = fullfile(fullSavePath, ['Final_LUT_' timeStampStr '.txt']);
lutMatPath = fullfile(fullSavePath, ['Final_LUT_' timeStampStr '.mat']);

try
    writetable(codeLUT, lutTxtPath, 'Delimiter', '\t');
    save(lutMatPath, 'codeLUT');
    fprintf('\n所有任务完成。最终结果已保存至:\n%s\n', fullSavePath);
catch ME
    warning(ME.identifier,'最终保存失败: %s', ME.message);
end

diary off;

