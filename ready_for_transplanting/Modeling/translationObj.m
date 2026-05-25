% function translationObj(mws,obj,xpos,ypos,zpos,Iscopy,repeatNum)
% %TRANSLATIONOBJ 平移物体
% 
% obj = ensure_cst_string(obj);
% 
% sCommand = '';
% sCommand = [sCommand 'With Transform'];
% sCommand = [sCommand 10 '.Reset'];
% sCommand = [sCommand 10 sprintf('.Name "%s"',obj)];
% sCommand = [sCommand 10 sprintf('.Vector "%.4f", "%.4f", "%.4f"',xpos,ypos,zpos)];
% sCommand = [sCommand 10 '.UsePickedPoints "False"'];
% sCommand = [sCommand 10 '.InvertPickedPoints "False"'];
% 
% if Iscopy
%     sCommand = [sCommand 10 '.MultipleObjects "True"'];
% 
% else
%     sCommand = [sCommand 10 '.MultipleObjects "False"'];
% end
% 
% sCommand = [sCommand 10 '.GroupObjects "False"'];
% sCommand = [sCommand 10 sprintf('.Repetitions "%d"',repeatNum)];
% 
% if Iscopy
%     sCommand = [sCommand 10 '.Destination ""'];
%     sCommand = [sCommand 10 '.Material ""'];
% end
% 
% sCommand = [sCommand 10 '.AutoDestination "True"'];
% sCommand = [sCommand 10 '.Transform "Shape", "Translate"'];
% sCommand = [sCommand 10 'End With'];
% 
% invoke(mws, 'AddToHistory',sprintf('transform: translate %s',obj),sCommand);
% end
% 
% 
function translationObj(mws, obj, xpos, ypos, zpos, Iscopy, repeatNum, newName)
%TRANSLATIONOBJ 平移物体 (增强版)
% 新增参数: newName (可选) - 如果提供了这个参数，复制时会直接重命名

obj = ensure_cst_string(obj);

% --- 检查可选参数 ---
if nargin < 8
    newName = ''; % 如果没传新名字，默认为空
end
% ------------------
sCommand = '';

if ~isempty(newName)
    sCommand = [sCommand 10 sprintf('Component.New "%s"', newName) 10];
end


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
    % --- 关键修改逻辑 ---
    if ~isempty(newName)
        % 如果指定了新名字：使用指定名字，关闭自动命名
        sCommand = [sCommand 10 sprintf('.Destination "%s"', newName)];
        sCommand = [sCommand 10 '.AutoDestination "False"'];
    else
        % 如果没指定：保持原有逻辑
        sCommand = [sCommand 10 '.Destination ""'];
        sCommand = [sCommand 10 '.AutoDestination "True"'];
    end
    sCommand = [sCommand 10 '.Material ""'];
end

sCommand = [sCommand 10 '.Transform "Shape", "Translate"'];
sCommand = [sCommand 10 'End With'];

invoke(mws, 'AddToHistory',sprintf('transform: translate %s',obj),sCommand);
end