classdef OFDM_Transceiver
    % OFDM_Transceiver - OFDM 发射接收器示例
    % OFDM_Transceiver - A sample OFDM transceiver that performs basic QPSK modulation,
    % pilot insertion and outputs a frequency-domain transmit signal.
    
    properties
        params          % 系统参数结构体 / System parameters
        PilotIndices    % 导频子载波索引 / Pilot subcarrier indices
    end
    
    methods
        function obj = OFDM_Transceiver(params)
            % 构造函数 / Constructor
            % 存储参数并根据算法参数设定导频间隔，计算导频子载波索引
            obj.params = params;
            pilotInterval = params.algo.PilotInterval;  % 导频间隔 / Pilot interval
            NumSubcarriers = params.sys.NumSubcarriers;
            % 选取每隔 pilotInterval 个子载波作为导频
            obj.PilotIndices = 1:pilotInterval:NumSubcarriers;
        end
        
        function [txSignal, pilotIndices] = Transmit(obj, bits)
            % Transmit - 对输入比特流进行 QPSK 调制，并映射到 OFDM 频域符号
            %
            % 输入:
            %   bits - 输入比特流 (column vector)
            %
            % 输出:
            %   txSignal     - 频域传输信号，尺寸为 [Nt, NumSubcarriers]
            %   pilotIndices - 导频子载波索引
            
            % 计算所需的 QPSK 符号数 = 发射天线数 * 子载波数
            Nt = obj.params.sys.Nt;
            NumSubcarriers = obj.params.sys.NumSubcarriers;
            numSymbols = Nt * NumSubcarriers;
            bitsPerSymbol = log2(obj.params.sys.ModOrder);  % 对于 QPSK，bitsPerSymbol = 2
            
            totalBits = numSymbols * bitsPerSymbol;
            if length(bits) < totalBits
                error('输入比特数不足，应至少 %d 个比特', totalBits);
            end
            % 仅取前 totalBits 个比特
            bits = bits(1:totalBits);
            
            % 将比特流重组为矩阵，每行代表一个符号对应的比特
            bitMatrix = reshape(bits, bitsPerSymbol, []).';
            % 将比特矩阵转换为十进制符号索引 (采用 MSB 优先)
            symbolIndices = bi2de(bitMatrix, 'left-msb');
            
            % QPSK 调制，采用 pi/4 相位偏移
            symbols = pskmod(symbolIndices, obj.params.sys.ModOrder, pi/4);
            
            % 将符号向量重排成 [Nt, NumSubcarriers] 的矩阵，每行对应一个发射天线
            txSignal = reshape(symbols, Nt, NumSubcarriers);
            
            % 返回导频子载波索引
            pilotIndices = obj.PilotIndices;
        end
        
        function rxBits = Receive(obj, rxSignal)
            % Receive - 简单示例接收函数，执行 OFDM 解调及 QPSK 解调
            % 此处仅作为占位实现，实际应用中需结合信道均衡及导频估计
            %
            % 输入:
            %   rxSignal - 接收到的频域信号，尺寸为 [Nr, NumSubcarriers]
            %
            % 输出:
            %   rxBits - 解调后的比特流 (列向量)
            
            % 此处简化处理，假设使用第一接收天线信号进行解调
            y = rxSignal(1, :);
            % QPSK 解调
            demodSymbols = pskdemod(y, obj.params.sys.ModOrder, pi/4);
            % 转换为二进制比特
            bitsMatrix = de2bi(demodSymbols, log2(obj.params.sys.ModOrder), 'left-msb');
            rxBits = bitsMatrix.';
            rxBits = rxBits(:);
        end
    end
end