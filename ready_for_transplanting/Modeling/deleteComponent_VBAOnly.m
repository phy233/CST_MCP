function scommand_out = deleteComponent_VBAOnly(command,obj)
%DELETECOMPONENT 删除整个形状的组件文件夹
%   
sCommend = sprintf('Component.Delete "%s"',obj);

scommand_out = [command 10 sCommend];
end

