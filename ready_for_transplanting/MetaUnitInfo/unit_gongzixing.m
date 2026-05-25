classdef unit_gongzixing

    % --- 常量属性 (Constant) ---
    % 这些值在所有实例中都是一样的，不可修改
    properties(Constant)
        unitSize = [13 13 3];
        freq = 8e9;
        codeNum = 4;
    end

    % --- 普通属性 (Properties) ---
    % 这里只定义变量名，或者赋简单的初始值
    properties
        IsMultiStruct = true;
        IsDirectModeling = true;
        % 这里只声明 codeParam 这个容器，不要在这里赋值
        codeParam
    end

    properties
        % 单元的几何参数
        a = 13;
        h = 1.5;
        w = 1.5;
        h_medal = 0.018;
        a_cly = 12;
        lx = 6.4;
    end

    % --- 方法 (Methods) ---
    methods
        % 构造函数：函数名必须与类名(unitParamsTest)完全一致
        % 只有在这里才能使用 'obj' 并进行逻辑运算
        function obj = unit_gongzixing()
            obj.codeParam = [];
        end

        % 直接建模
        function codeModeling(obj,mws, this_code, this_center, unit_name)

            if ~check_material_exists(mws,'material1')
                defineMaterial(mws,'material1',3,1,0.001,20,50);
            end

            % 搭建基座
            currentPoint = this_center+[0,0,0];
            activateWCS(mws,[0,0,1],currentPoint,[1,0,0],1);
            defineBrick(mws,'base1',unit_name,[0,0,0],obj.a,obj.a,obj.h,'material1');
            defineBrick(mws,'gnd',unit_name,[0,0,0],obj.a,obj.a,0,'PEC');
            currentPoint = currentPoint+[0,0,obj.h];
            activateWCS(mws,[0,0,1],currentPoint,[1,0,0],1);
            defineBrick(mws,'base2',unit_name,[0,0,0],obj.a,obj.a,obj.h,'material1');
            defineCylinder(mws,unit_name,'base3','material1',obj.a_cly/2,0,obj.h,'z',[0,0,0]);
            substractObj(mws,unit_name,'base2',unit_name,'base3');
            defineCylinder(mws,unit_name,'codebase','material1',obj.a_cly/2,0,obj.h,'z',[0,0,0]);
            currentPoint = currentPoint+[0,0,obj.h/2];
            activateWCS(mws,[0,0,1],currentPoint,[1,0,0],1);
            switch this_code
                case 1
                    defineBrick(mws,'medalx',unit_name,[0,0,0],6.4,1.5,obj.h_medal,'PEC');
                    defineBrick(mws,'medaly',unit_name,[0,0,0],1.5,2,obj.h_medal,'PEC');
                    addObj(mws,unit_name,'medalx',unit_name,'medaly');
                case 2
                    defineBrick(mws,'medalx',unit_name,[0,0,0],6.4,1.5,obj.h_medal,'PEC');
                    defineBrick(mws,'medaly',unit_name,[0,0,0],1.5,5,obj.h_medal,'PEC');
                    addObj(mws,unit_name,'medalx',unit_name,'medaly');
                case 3
                    defineBrick(mws,'medalx',unit_name,[0,0,0],6.4,1.5,obj.h_medal,'PEC');
                    defineBrick(mws,'medaly',unit_name,[0,0,0],1.5,8,obj.h_medal,'PEC');
                    addObj(mws,unit_name,'medalx',unit_name,'medaly');
                case 4
                    defineBrick(mws,'medalx',unit_name,[0,0,0],6.4,1.5,obj.h_medal,'PEC');
                    defineBrick(mws,'medaly',unit_name,[0,0,0],1.5,10,obj.h_medal,'PEC');
                    addObj(mws,unit_name,'medalx',unit_name,'medaly');
                otherwise
                    error('输入的编码数不正确，从1开始，这里是2bit');
            end
        end
    end
end