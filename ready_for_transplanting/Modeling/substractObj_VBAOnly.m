function scommend_out = substractObj_VBAOnly(commend,componentName1,objName1,componentName2,objName2)
%substractObj 布尔运算减
% 第一个对象是被减的，第二个对象是要被扣掉的

componentName1 = ensure_cst_string(componentName1);
objName1 = ensure_cst_string(objName1);
componentName2 = ensure_cst_string(componentName2);
objName2 = ensure_cst_string(objName2);

scomment = sprintf('Solid.Subtract "%s:%s", "%s:%s"',componentName1,objName1,componentName2,objName2);

scommend_out = [commend 10 scomment];

end

