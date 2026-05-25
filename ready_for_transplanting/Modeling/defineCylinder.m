function defineCylinder(mws,componentName,objName,material,outR,inR,height,direction,centerPoint)
%defineCylinder 新建一个圆柱体

componentName = ensure_cst_string(componentName);
objName = ensure_cst_string(objName);

if ~check_material_exists(mws,material)
    error('材料 %s 不存在，先去新建材料',material);
end

% xcenter = centerPoint(1);
% ycenter = centerPoint(2);
% zrange = [centerPoint(3)-height/2,centerPoint(3)+height/2];

scomment = '';
scomment = ['With Cylinder'];
scomment = [scomment 10 '.Reset'];
scomment = [scomment 10 sprintf('.Name "%s"',objName)];
scomment = [scomment 10 sprintf('.Component "%s"',componentName)];
scomment = [scomment 10 sprintf('.Material "%s"',material)];
scomment = [scomment 10 sprintf('.OuterRadius "%.4f"',outR)];
scomment = [scomment 10 sprintf('.InnerRadius "%.4f"',inR)];
scomment = [scomment 10 sprintf('.Axis "%s"',direction)];

switch direction
    case 'x'

        xcenter = [centerPoint(1)-height/2,centerPoint(1)+height/2];
        ycenter = centerPoint(2);
        zrange = centerPoint(3);


        scomment = [scomment 10 sprintf('.Zcenter "%.4f"',zrange)];
        scomment = [scomment 10 sprintf('.Xrange "%.4f", "%.4f"',xcenter(1),xcenter(2))];
        scomment = [scomment 10 sprintf('.Ycenter "%.4f"',ycenter)];

    case 'y'

        xcenter = centerPoint(1);
        ycenter = [centerPoint(2)-height/2,centerPoint(2)+height/2];
        zrange = centerPoint(3);


        scomment = [scomment 10 sprintf('.Zcenter "%.4f"',zrange)];
        scomment = [scomment 10 sprintf('.Xcenter "%.4f"',xcenter)];
        scomment = [scomment 10 sprintf('.Yrange "%.4f", "%.4f"',ycenter(1),ycenter(2))];

    case 'z'

        xcenter = centerPoint(1);
        ycenter = centerPoint(2);
        zrange = [centerPoint(3)-height/2,centerPoint(3)+height/2];


        scomment = [scomment 10 sprintf('.Zrange "%.4f", "%.4f"',zrange(1),zrange(2))];
        scomment = [scomment 10 sprintf('.Xcenter "%.4f"',xcenter)];
        scomment = [scomment 10 sprintf('.Ycenter "%.4f"',ycenter)];

    otherwise
        error('错误的朝向%s，请重试',direction);

end

% scomment = [scomment 10 sprintf('.Zrange "%.4f", "%.4f"',zrange(1),zrange(2))];
% scomment = [scomment 10 sprintf('.Xcenter "%.4f"',xcenter)];
% scomment = [scomment 10 sprintf('.Ycenter "%.4f"',ycenter)];
scomment = [scomment 10 '.Segments "0"'];
scomment = [scomment 10 '.Create'];
scomment = [scomment 10 'End With'];

invoke(mws,'AddToHistory',sprintf('define cylinder: %s:%s',componentName,objName),scomment);

end

