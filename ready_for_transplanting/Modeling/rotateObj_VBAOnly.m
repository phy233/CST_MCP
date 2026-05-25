function scommend_out = rotateObj_VBAOnly(mws,commend,componentName,objName,center,angle,Iscopy)
%ROTATEOBJ 旋转物体

centerx = center(1);
centery = center(2);
centerz = center(3);
angelx = angle(1);
angely = angle(2);
angelz = angle(3);

componentName = ensure_cst_string(componentName);
objName = ensure_cst_string(objName);

if ~ensure_component_exist(mws,componentName)
    error('选定的组件%s不存在，请检查',componentName);
end

scomment = 'With Transform';
scomment = [scomment 10 '.Reset'];
scomment = [scomment 10 sprintf('.Name "%s:%s"',componentName,objName)];
scomment = [scomment 10 '.Origin "Free"'];
scomment = [scomment 10 sprintf('.Center "%.4f", "%.4f", "%.4f"',centerx,centery,centerz)];
scomment = [scomment 10 sprintf('.Angle "%.2f", "%.2f", "%.2f"',angelx,angely,angelz)];

if Iscopy
    scomment = [scomment 10 '.MultipleObjects "True"'];
else
    scomment = [scomment 10 '.MultipleObjects "False"'];
end

scomment = [scomment 10 '.GroupObjects "False"'];
scomment = [scomment 10 '.Repetitions "1"'];
scomment = [scomment 10 '.MultipleSelection "False"'];
scomment = [scomment 10 '.Destination ""'];
scomment = [scomment 10 '.Material ""'];
scomment = [scomment 10 '.AutoDestination "True"'];
scomment = [scomment 10 '.Transform "Shape", "Rotate"'];
scomment = [scomment 10 'End With'];

scommend_out = [commend 10 scomment];

end

