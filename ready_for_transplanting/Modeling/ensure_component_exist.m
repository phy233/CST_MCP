function isExist= ensure_component_exist(mws,componentName)
%ensure_component_exist 检查输入的组件是否存在
%

componentName = ensure_cst_string(componentName);
tmp = invoke(mws,'Component');

isExist = tmp.invoke('DoesExist',componentName);

release(tmp);
end

