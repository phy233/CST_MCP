function parameterlist = getParameterList(mws)
%GETPARAMETERLIST 获取当前工程文件下的所有参数和参数值

% 初始化输出为空元胞
parameterlist = cell(0);

% 采取COM命令形式获取参数，不写入历史树
% 获取目前参数的个数
parameterNum = invoke(mws,'GetNumberOfParameters');

% 用循环逐个读取参数，注意按照官方手册里参数序号从0开始，记得减一
for idx = 1:parameterNum
    currentParameterIndex = idx-1;
    currentParameterName = invoke(mws,'GetParameterName',sprintf('%d',currentParameterIndex));
    currentParameterValue = invoke(mws,'GetParameterNValue',sprintf('%d',currentParameterIndex));
    parameterlist{idx} = {currentParameterName, currentParameterValue};
end

end

