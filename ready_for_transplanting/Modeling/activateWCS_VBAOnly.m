function scommand_out = activateWCS_VBAOnly(command,SetNormal,SetOrigin,SetUVector)
%ACTIVATEWCS 激活坐标系，只拼接VBA命令


%SetNormal = [0 0 1]
%SetOrigin = [0 0 0]
%SetUVector = [1 0 0]
%Activate = 1 or 0;


scommand = 'With WCS';
scommand = [scommand 10 sprintf('.SetNormal "%.2f", "%.2f", "%.2f"',SetNormal(1),SetNormal(2),SetNormal(3))];
scommand = [scommand 10 sprintf('.SetOrigin "%.2f", "%.2f", "%.2f"',SetOrigin(1),SetOrigin(2),SetOrigin(3))];
scommand = [scommand 10 sprintf('.SetUVector "%.2f", "%.2f", "%.2f"',SetUVector(1),SetUVector(2),SetUVector(3))];
scommand = [scommand 10 'End With'];

scommand_out = [command 10 scommand];

end

