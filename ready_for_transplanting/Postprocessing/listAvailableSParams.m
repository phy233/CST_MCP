function availableList = listAvailableSParams(mws)
% LISTAVAILABLESPARAMS 列出当前 CST 工程中所有计算好的 S 参数名称
% 返回值 availableList 是一个字符串 Cell 数组

    rt = invoke(mws, 'ResultTree');
    baseFolder = '1D Results\S-Parameters';
    availableList = {};
    
    % 1. 检查文件夹是否存在
    if ~invoke(rt, 'DoesTreeItemExist', baseFolder)
        warning('CST 中没有找到 S-Parameters 文件夹。');
        return;
    end
    
    % 2. 遍历文件夹下的所有子项
    childName = invoke(rt, 'GetFirstChildName', baseFolder);
    
    fprintf('=== CST 中可用的 S 参数列表 ===\n');
    idx = 1;
    while ~isempty(childName)
        availableList{end+1} = childName;
        fprintf('  [%d] %s\n', idx, childName);
        
        % 获取下一个
        currentPath = childName;
        childName = invoke(rt, 'GetNextItemName', currentPath);
        idx = idx + 1;
    end
    fprintf('=================================\n');
    
    release(rt);
end