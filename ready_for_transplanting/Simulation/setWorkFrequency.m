function setWorkFrequency(mws,freq)
%SETWORKFREQUENCY 设定仿真频率范围
%   此处显示详细说明
freqLow = freq(1);
freqHigh = freq(2);
sCommand = '';
sCommand = [sCommand 'Solver.FrequencyRange '  num2str(freqLow) ',' num2str(freqHigh) ];
invoke(mws, 'AddToHistory','define frequency range', sCommand);
end

