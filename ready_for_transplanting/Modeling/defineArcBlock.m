function defineArcBlock(mws,componentName,objName,material,thick,width,thita,centerPoint,startPoint,orientation)
%DEFINEARCBLOCK 新建一个圆环
%   此处显示详细说明

tmpObjName = 'tmpObjName';
tmpComName = 'tmpComName';

componentName = ensure_cst_string(componentName);
objName = ensure_cst_string(objName);
material = ensure_cst_string(material);

if ~check_material_exists(mws,material)
    error('材料%s不存在，请检查',material)
end

defineArc(mws,orientation,centerPoint,startPoint,thita,tmpComName,tmpObjName);

scomment = 'With TraceFromCurve';
scomment = [scomment 10 '.Reset'];
scomment = [scomment 10 sprintf('.Name "%s"',objName)];
scomment = [scomment 10 sprintf('.Component "%s"',componentName)];
scomment = [scomment 10 sprintf('.Material "%s"',material)];
scomment = [scomment 10 sprintf('.Curve "%s:%s"',tmpComName,tmpObjName)];
scomment = [scomment 10 sprintf('.Thickness "%.2f"',thick)];
scomment = [scomment 10 sprintf('.Width "%.2f"',width)];
scomment = [scomment 10 '.RoundStart "False"'];
scomment = [scomment 10 '.RoundEnd "False"'];
scomment = [scomment 10 '.DeleteCurve "True"'];
scomment = [scomment 10 '.GapType "2"'];
scomment = [scomment 10 '.Create'];
scomment = [scomment 10 'End With'];

scomment = [scomment 10 sprintf('Curve.DeleteCurve "%s"',tmpComName)];

mws.invoke('AddToHistory',sprintf('create arc block:%s:%s',componentName,objName),scomment);

end

