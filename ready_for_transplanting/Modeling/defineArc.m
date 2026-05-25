% function defineArc(mws, orientation, centerPoint, startPoint, thita, componentName, objName)
% %DEFINEARC 新建一段圆弧
% 
% if ~(isequal(orientation, 'Clockwise')||isequal(orientation, 'CounterClockwise'))
%     error('取向设置错误，当前为%s，必须为Clockwise或者CounterClockwise',orientation);
% end
% 
% componentName = ensure_cst_string(componentName);
% objName = ensure_cst_string(objName);
% 
% relativeX = startPoint(1)-centerPoint(1);
% relativeY = startPoint(2)-centerPoint(2);
% 
% normalVec = [0 0 1];
% UVec = [1 0 0];
% activateWCS(mws,normalVec,centerPoint,UVec,1);
% 
% scommend = 'With Arc';
% scommend = [scommend 10 '.Reset'];
% scommend = [scommend 10 sprintf('.Name "%s"',objName)];
% scommend = [scommend 10 sprintf('.Curve "%s"',componentName)];
% scommend = [scommend 10 sprintf('.Orientation "%s"',orientation)];
% scommend = [scommend 10 '.XCenter "0.0"'];
% scommend = [scommend 10 '.YCenter "0.0"'];
% scommend = [scommend 10 sprintf('.X1 "%.2f"',relativeX)];
% scommend = [scommend 10 sprintf('.Y1 "%.2f"',relativeY)];
% scommend = [scommend 10 '.X2 "0.0"'];
% scommend = [scommend 10 '.Y2 "0.0"'];
% scommend = [scommend 10 sprintf('.Angle "%.2f"',thita)];
% scommend = [scommend 10 '.UseAngle "True"'];
% scommend = [scommend 10 '.Segments "0"'];
% scommend = [scommend 10 '.Create'];
% scommend = [scommend 10 'End With'];
% 
% mws.invoke('AddToHistory', sprintf('create arc:%s:%s',componentName,objName), scommend);
% 
% activateWCS(mws,normalVec,centerPoint,UVec,0);
% 
% end
% 

function defineArc(mws, orientation, centerPoint, startPoint, thita, componentName, objName)
%DEFINEARC 新建一段圆弧 (修正版：适配阵列建模)
% 注意：此函数不再移动WCS，而是直接在当前激活的WCS（局部坐标系）中绘图。
% 请确保在调用此函数前，通过阵列代码将WCS移动到了正确的位置。

if ~(isequal(orientation, 'Clockwise')||isequal(orientation, 'CounterClockwise'))
    error('取向设置错误，当前为%s，必须为Clockwise或者CounterClockwise',orientation);
end

componentName = ensure_cst_string(componentName);
objName = ensure_cst_string(objName);

% --- 修改点 1: 删除 WCS 激活与相对坐标计算 ---
% 原代码通过移动WCS到圆心，使XCenter变为0。
% 新代码直接使用当前WCS下的坐标。
% 假设传入的 centerPoint 和 startPoint 都是相对于当前阵列单元 WCS 的坐标。

scommend = 'With Arc';
scommend = [scommend 10 '.Reset'];
scommend = [scommend 10 sprintf('.Name "%s"',objName)];
scommend = [scommend 10 sprintf('.Curve "%s"',componentName)];
scommend = [scommend 10 sprintf('.Orientation "%s"',orientation)];

% --- 修改点 2: 直接使用传入的坐标 ---
% 圆心坐标 (在当前WCS下)
scommend = [scommend 10 sprintf('.XCenter "%.4f"', centerPoint(1))];
scommend = [scommend 10 sprintf('.YCenter "%.4f"', centerPoint(2))];

% 起始点坐标 (在当前WCS下)
% CST的Arc定义通常需要圆心(XCenter, YCenter)和第一点(X1, Y1)
scommend = [scommend 10 sprintf('.X1 "%.4f"', startPoint(1))];
scommend = [scommend 10 sprintf('.Y1 "%.4f"', startPoint(2))];

% 第二点通常设为0，通过Angle控制
scommend = [scommend 10 '.X2 "0.0"'];
scommend = [scommend 10 '.Y2 "0.0"'];

scommend = [scommend 10 sprintf('.Angle "%.2f"',thita)];
scommend = [scommend 10 '.UseAngle "True"'];
scommend = [scommend 10 '.Segments "0"'];
scommend = [scommend 10 '.Create'];
scommend = [scommend 10 'End With'];

mws.invoke('AddToHistory', sprintf('create arc:%s:%s',componentName,objName), scommend);

% --- 修改点 3: 删除 WCS 重置 ---
% activateWCS(mws,normalVec,centerPoint,UVec,0); %这一行删掉，避免重置回Global

end
