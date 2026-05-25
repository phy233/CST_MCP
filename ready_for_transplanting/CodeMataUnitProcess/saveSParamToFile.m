%% --- 辅助函数：将保存逻辑封装，避免代码重复 ---
function saveSParamToFile(freq, S_Re, S_Im, saveDir, resName, p1Name, p1Val, p2Name, p2Val)
% 1. 清洗结果名称 (去掉逗号括号)
safeResName = replace(resName, {',', '(', ')'}, '_');

% 2. 构造包含参数值的文件名 (这是最重要的！)
% 格式: S_SZmax1_lx_2.00_ly_3.00.txt
fName = sprintf('S_%s_%s_%.2f_%s_%.2f.txt', ...
    safeResName, p1Name, p1Val, p2Name, p2Val);

% 3. 完整路径
fullP = fullfile(saveDir, fName);

% 4. 保存
%T = table(freq, S_Re, S_Im, 'VariableNames', {'Freq', 'Re', 'Im'});
% 使用 (:) 确保无论输入是横是竖，都转为 N行1列
T = table(freq(:), S_Re(:), S_Im(:), 'VariableNames', {'Freq', 'Re', 'Im'});
writetable(T, fullP, 'Delimiter', '\t');
end