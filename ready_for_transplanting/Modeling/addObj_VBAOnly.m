function scomment_out = addObj_VBAOnly(command,componentName1,objName1,componentName2,objName2)
%ADDOBJ_NOADDTOHISTORY 布尔运算加，但是只生成VBA指令不执行


componentName1 = ensure_cst_string(componentName1);
objName1 = ensure_cst_string(objName1);
componentName2 = ensure_cst_string(componentName2);
objName2 = ensure_cst_string(objName2);

scomment = sprintf('Solid.Add "%s:%s", "%s:%s"',componentName1,objName1,componentName2,objName2);

scomment_out = [command 10 scomment];

end

