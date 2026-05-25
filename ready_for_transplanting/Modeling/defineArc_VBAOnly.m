function scommend_out = defineArc_VBAOnly(command, orientation, centerPoint, startPoint, thita, componentName, objName)
%DEFINEARCBLOCK_VBAOnly 新建一个圆环,只输出VBA命令不执行
%   此处显示详细说明


if ~(isequal(orientation, 'Clockwise')||isequal(orientation, 'CounterClockwise'))
    error('取向设置错误，当前为%s，必须为Clockwise或者CounterClockwise',orientation);
end

componentName = ensure_cst_string(componentName);
objName = ensure_cst_string(objName);

relativeX = startPoint(1)-centerPoint(1);
relativeY = startPoint(2)-centerPoint(2);

normalVec = [0 0 1];
UVec = [1 0 0];

scommend_tmp1 = activateWCS_VBAOnly(command,normalVec,centerPoint,UVec);

scommend = [scommend_tmp1 10 'With Arc'];
scommend = [scommend 10 '.Reset'];
scommend = [scommend 10 sprintf('.Name "%s"',objName)];
scommend = [scommend 10 sprintf('.Curve "%s"',componentName)];
scommend = [scommend 10 sprintf('.Orientation "%s"',orientation)];
scommend = [scommend 10 '.XCenter "0.0"'];
scommend = [scommend 10 '.YCenter "0.0"'];
scommend = [scommend 10 sprintf('.X1 "%.2f"',relativeX)];
scommend = [scommend 10 sprintf('.Y1 "%.2f"',relativeY)];
scommend = [scommend 10 '.X2 "0.0"'];
scommend = [scommend 10 '.Y2 "0.0"'];
scommend = [scommend 10 sprintf('.Angle "%.2f"',thita)];
scommend = [scommend 10 '.UseAngle "True"'];
scommend = [scommend 10 '.Segments "0"'];
scommend = [scommend 10 '.Create'];
scommend = [scommend 10 'End With'];

scommend_out = activateWCSGlobal_VBAOnly(scommend);

end

