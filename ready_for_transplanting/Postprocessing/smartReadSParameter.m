function [freq, S_Re, S_Im] = smartReadSParameter(mws,targetName)

rt = invoke(mws, 'ResultTree');
baseFolder = '1D Results\S-Parameters';

% 1. 自动补全路径
% 如果用户只传了 'S1,1'，我们自动拼成 '1D Results\S-Parameters\S1,1'
% 这样调用起来更方便
if ~contains(targetName, '1D Results')
    fullTreePath = [baseFolder, '\', targetName];
else
    fullTreePath = targetName;
end

% 2. 检查该结果是否存在
if ~invoke(rt, 'DoesTreeItemExist', fullTreePath)
    % 如果找不到，自动调用列表函数帮用户找原因
    fprintf('错误：在 CST 中找不到路径 "%s"。\n', fullTreePath);
    listAvailableSParams(mws); % 列出可用的供参考
    error('请从上述列表中选择正确的名称。');
end

% 3. 获取内部文件路径 (解决 File not exist 问题)
internalPath = invoke(rt, 'GetFileFromTreeItem', fullTreePath);

if isempty(internalPath)
    error('找到树节点 "%s"，但无法获取内部数据路径。', fullTreePath);
end


% 5. 读取数据
resObj = invoke(mws, 'Result1DComplex', internalPath);

freq = invoke(resObj, 'GetArray', 'x');
S_Re = invoke(resObj, 'GetArray', 'yre');
S_Im = invoke(resObj, 'GetArray', 'yim');

release(resObj);
release(rt);
end