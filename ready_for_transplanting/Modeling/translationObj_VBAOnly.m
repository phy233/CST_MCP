function scommend_out = translationObj_VBAOnly(commend,obj,xpos,ypos,zpos,Iscopy,repeatNum)
%TRANSLATIONOBJ 平移物体

obj = ensure_cst_string(obj);

sCommand = '';
sCommand = [sCommand 'With Transform'];
sCommand = [sCommand 10 '.Reset'];
sCommand = [sCommand 10 sprintf('.Name "%s"',obj)];
sCommand = [sCommand 10 sprintf('.Vector "%.4f", "%.4f", "%.4f"',xpos,ypos,zpos)];
sCommand = [sCommand 10 '.UsePickedPoints "False"'];
sCommand = [sCommand 10 '.InvertPickedPoints "False"'];

if Iscopy
    sCommand = [sCommand 10 '.MultipleObjects "True"'];

else
    sCommand = [sCommand 10 '.MultipleObjects "False"'];
end

sCommand = [sCommand 10 '.GroupObjects "False"'];
sCommand = [sCommand 10 sprintf('.Repetitions "%d"',repeatNum)];

if Iscopy
    sCommand = [sCommand 10 '.Destination ""'];
    sCommand = [sCommand 10 '.Material ""'];
end

sCommand = [sCommand 10 '.AutoDestination "True"'];
sCommand = [sCommand 10 '.Transform "Shape", "Translate"'];
sCommand = [sCommand 10 'End With'];


scommend_out = [commend 10 sCommand];

end


