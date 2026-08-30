function [H, pathInfo] = CDL_Channel(params)
% CDL_Channel - 基于随机多径模型生成频域信道矩阵及路径信息
% CDL_Channel - Generate frequency-domain channel matrix and path info using a
%              random multipath model (mimicking 3GPP TR 38.901 CDL)
%
% 输入参数 (Input Arguments):
%   params - 包含系统参数和信道参数的结构体，主要字段包括：
%       params.sys.fc             : 载波频率 (Carrier Frequency)
%       params.sys.BW             : 系统带宽 (Bandwidth)
%       params.sys.NumSubcarriers : OFDM 子载波数 (Number of Subcarriers)
%       params.sys.Nt             : 发射天线数 (Number of Tx antennas)
%       params.sys.Nr             : 接收天线数 (Number of Rx antennas)
%
%       params.channel.DelaySpread: 时延扩展 (Delay Spread, e.g. 100e-9)
%       params.channel.NumPaths   : 路径数 (Number of Paths, e.g. 6)
%
% 输出参数 (Output Arguments):
%   H        - 频域信道矩阵，尺寸为 [Nr, Nt, NumSubcarriers]
%   pathInfo - 包含路径延时、AoD、AoA及路径增益信息的结构体

%% 1. 获取系统参数 / Get system parameters
fc = params.sys.fc;                    % Carrier frequency (Hz)
BW = params.sys.BW;                    % Bandwidth (Hz)
NumSubcarriers = params.sys.NumSubcarriers;  % Number of subcarriers
Nt = params.sys.Nt;                    % Number of transmit antennas
Nr = params.sys.Nr;                    % Number of receive antennas

%% 2. 获取信道参数 / Get channel parameters
DelaySpread = params.channel.DelaySpread;  % Maximum delay spread (s)
NumPaths = params.channel.NumPaths;          % Number of multipath components

%% 3. 生成路径参数 / Generate path parameters
% 路径延时：均匀分布在 [0, DelaySpread] 内，并按从小到大排序
% Path delays: uniformly distributed between 0 and DelaySpread, sorted
pathDelays = sort(rand(NumPaths,1) * DelaySpread);

% 发射角 (AoD) 和接收角 (AoA)：均匀分布在 [0, 2*pi]
AoD = rand(NumPaths,1) * 2*pi;
AoA = rand(NumPaths,1) * 2*pi;

%% 4. 生成路径增益 / Generate path gains
% 对于每条路径，为每对天线生成独立的 Rayleigh 衰落系数
% 生成尺寸为 [Nr, Nt, NumPaths] 的复数矩阵，每个元素均值为0，方差归一化
pathGains = (randn(Nr, Nt, NumPaths) + 1j*randn(Nr, Nt, NumPaths)) / sqrt(2*NumPaths);

%% 5. 构建频域信道矩阵 / Build frequency-domain channel matrix
% 每个子载波频率间隔为 deltaF = BW/NumSubcarriers
deltaF = BW / NumSubcarriers;
H = zeros(Nr, Nt, NumSubcarriers);

for k = 1:NumSubcarriers
    % 当前子载波的频率偏移（基带假设）： f_k = (k-1)*deltaF
    f_k = (k-1) * deltaF;
    H_k = zeros(Nr, Nt);
    for p = 1:NumPaths
        % 对于每条路径 p，计算相位补偿 exp(-j*2*pi*f_k*tau_p)
        phaseTerm = exp(-1j * 2*pi * f_k * pathDelays(p));
        % 累加所有路径贡献：各路径增益乘以相位补偿
        H_k = H_k + pathGains(:,:,p) * phaseTerm;
    end
    H(:,:,k) = H_k;
end

%% 6. 构建输出路径信息结构体 / Build path information structure
pathInfo = struct(...
    'Delays', pathDelays, ...    % 路径延时 (s)
    'AoD', AoD, ...              % 发射角 (rad)
    'AoA', AoA, ...              % 接收角 (rad)
    'PathGains', pathGains ...   % 路径增益
);

end