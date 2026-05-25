function IsSuccess = updateStructure(mws,IsFullRebuild)
%UPDATESTRUCTURE 更新结构
%   此处显示详细说明

if IsFullRebuild
    IsSuccess = mws.invoke('RebuildOnParametricChange','True','False');
else
    IsSuccess = mws.invoke('RebuildOnParametricChange','False','False');

end

