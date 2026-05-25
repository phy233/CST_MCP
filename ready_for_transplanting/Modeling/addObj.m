function addObj(mws,componentName1,objName1,componentName2,objName2)
%ADDOBJ 布尔运算加

componentName1 = ensure_cst_string(componentName1);
objName1 = ensure_cst_string(objName1);
componentName2 = ensure_cst_string(componentName2);
objName2 = ensure_cst_string(objName2);

scomment = sprintf('Solid.Add "%s:%s", "%s:%s"',componentName1,objName1,componentName2,objName2);

invoke(mws,'AddToHistory',sprintf('boolen add shapes:"%s:%s", "%s:%s"',componentName1,objName1,componentName2,objName2),scomment);
end

