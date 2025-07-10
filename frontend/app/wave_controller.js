// 波浪动画控制器
class WaveController {
    constructor() {
        this.waves = document.querySelectorAll('.wave');
        this.isAnimating = false;
        this.animationSpeed = 1.0; // 动画速度倍数
        this.aniSpeed = 1.0; // JavaScript动画速度（像素/帧）
        this.isUsingJSAnimation = false; // 是否使用JavaScript动画
        this.resizeTimeout = null; // 防抖定时器
        this.init();
    }

    init() {
        // 默认使用JavaScript动画，因为CSS动画已被删除
        this.isUsingJSAnimation = true;
        
        // 初始化波浪动画
        this.startJSAnimation();
        
        // 监听GPU使用率变化来控制波浪速度
        this.setupGPUListener();
        
        // 使用ResizeObserver监测聊天框尺寸变化
        this.setupResizeObserver();
    }
    
    startAnimation() {
        // 这个方法不再需要，因为默认使用JavaScript动画
        console.log('波浪动画已启动（JavaScript模式）');
    }

    stopAnimation() {
        // 这个方法不再需要，因为默认使用JavaScript动画
        console.log('波浪动画已暂停（JavaScript模式）');
    }

    setSpeed(speed) {
        // 这个方法不再需要，因为默认使用JavaScript动画
        this.setSpeedWithJSAnimation(speed);
    }

    getBaseDuration(waveIndex) {
        // 返回基础动画时长
        return 8; // 单层波浪固定8秒
    }

    setupGPUListener() {
        // 监听GPU使用率变化
        window.addEventListener('gpu-usage-update', (event) => {
            const gpuUsage = event.detail.usage;
            const vramUsage = event.detail.vram || gpuUsage; // 如果没有显存数据，使用GPU使用率
            this.updateWaveSpeed(gpuUsage);
            this.updateWaveHeight(vramUsage);
        });
    }

    updateWaveSpeed(gpuUsage) {
        // 根据GPU运算使用率调整波浪速度
        // GPU使用率越高，波浪越快
        const speed = 1 + (gpuUsage/100) * 9; // 0.1x 到 1.0x
        
        // 使用JavaScript动画
        this.setSpeedWithJSAnimation(speed);
    }

    updateWaveHeight(vramUsage) {
        // 根据显存使用率调整波浪位置和背景高度
        // 波浪高度 = (显存使用率 / 100) * 背景层高度
        const chatBackground = document.getElementById('chat-background');
        if (!chatBackground) return;
        
        const chatBackgroundHeight = chatBackground.offsetHeight;
        const maxHeight = 120; // 波浪图片原始高度
        
        // 计算波浪高度：显存使用率占背景层高度的百分比
        const height = (vramUsage / 100) * chatBackgroundHeight;
        
        // 波浪底部位置：总高度减去波浪高度的1/3，视觉效果更好
        const waveBottom = Math.max(0, height - maxHeight/3);
        
        // 设置CSS变量
        const waveContainer = document.querySelector('.wave-container');
        if (waveContainer) {
            waveContainer.style.setProperty('--wave-height', `${height}px`);
            waveContainer.style.setProperty('--wave-bottom', `${waveBottom}px`);
        }
    }

    // 设置波浪高度
    setWaveHeight(height) {
        const waveContainer = document.querySelector('.wave-container');
        if (waveContainer) {
            const maxHeight = 120; // 图片原始高度
            const waveBottom = Math.max(0, height - maxHeight/3);
            // 同时设置波浪和背景的位置和高度
            waveContainer.style.setProperty('--wave-height', `${height}px`);
            waveContainer.style.setProperty('--wave-bottom', `${waveBottom}px`);
        }
    }
    
    // 根据聊天内容高度重新计算波浪高度
    recalculateWaveHeight() {
        const chatBackground = document.getElementById('chat-background');
        if (!chatBackground) return;
        
        const chatBackgroundHeight = chatBackground.offsetHeight;
        const currentHeight = this.getWaveHeight();
        const percentage = (currentHeight / chatBackgroundHeight) * 100;
        
        this.updateWaveHeight(percentage);
    }

    // 获取当前波浪高度
    getWaveHeight() {
        const waveContainer = document.querySelector('.wave-container');
        if (waveContainer) {
            const height = getComputedStyle(waveContainer).getPropertyValue('--wave-height');
            return parseInt(height) || 120;
        }
        return 120;
    }

    // JavaScript动画控制方法（推荐方案）
    setSpeedWithJSAnimation(speed) {
        this.animationSpeed = Math.max(1, Math.min(10.0, speed));
        this.aniSpeed = this.animationSpeed * 0.5; // 将速度转换为像素/帧
        
        if (!this.isUsingJSAnimation) {
            this.startJSAnimation();
        }
        
        console.log(`JavaScript波浪动画速度设置为: ${this.animationSpeed}x (${this.aniSpeed}px/帧)`);
    }
    
    startJSAnimation() {
        // 如果已经在运行，先停止
        if (this.isUsingJSAnimation) {
            this.stopJSAnimation();
        }
        
        this.isUsingJSAnimation = true;
        
        // 停止CSS动画
        this.waves.forEach(wave => {
            wave.style.animation = 'none';
        });
        
        // 初始化波浪位置 - 修复位置设置
        const waveLength = this.waves[0].offsetWidth;// 波浪长度比容器长40px
        
        this.waves[0].style.transform = 'translateX(0px)'; // 第一个波浪从容器左边开始
        this.waves[1].style.transform = `translateX(${waveLength}px)`; // 第二个波浪从容器内部开始，留出40px重叠
        
        // 开始JavaScript动画循环
        this.jsAnimationLoop();
        
        console.log('JavaScript波浪动画已启动');
    }
    
    jsAnimationLoop() {
        if (!this.isUsingJSAnimation) return;
        
        const waveLength = this.waves[0].offsetWidth;// 波浪长度比容器长40px
        
        this.waves.forEach((wave, index) => {
            // 获取当前位置
            const computedStyle = getComputedStyle(wave);
            const transform = computedStyle.transform;
            let currentX = 0;
            
            if (transform && transform !== 'none') {
                const matrix = transform.match(/matrix.*\((.+)\)/);
                if (matrix) {
                    const values = matrix[1].split(', ');
                    currentX = parseFloat(values[4]) || 0;
                }
            }
            
            // 移动波浪
            const newX = currentX - this.aniSpeed;
            
            // 检查波浪尾部是否超出容器20px
            const waveTail = newX + waveLength; // 波浪尾部位置
            if (waveTail < -20) {
                // 找到另一个波浪的尾部位置
                const otherWave = this.waves[index === 0 ? 1 : 0];
                const otherTransform = getComputedStyle(otherWave).transform;
                let otherX = 0;
                
                if (otherTransform && otherTransform !== 'none') {
                    const matrix = otherTransform.match(/matrix.*\((.+)\)/);
                    if (matrix) {
                        const values = matrix[1].split(', ');
                        otherX = parseFloat(values[4]) || 0;
                    }
                }
                
                // 将当前波浪放在另一个波浪的尾部后面
                const otherWaveTail = otherX + waveLength;
                if (index === 0) {
                    wave.style.transform = `translateX(${otherWaveTail - this.aniSpeed}px)`;
                } else {
                    wave.style.transform = `translateX(${otherWaveTail}px)`;
                }
                
            } else {
                wave.style.transform = `translateX(${newX}px)`;
            }
        });
        
        // 继续下一帧
        requestAnimationFrame(() => this.jsAnimationLoop());
    }
    
    stopJSAnimation() {
        this.isUsingJSAnimation = false;
        
        // 恢复CSS动画
        this.waves.forEach((wave, index) => {
            wave.style.animation = '';
            wave.style.transform = '';
        });
        
        console.log('JavaScript波浪动画已停止');
    }

    // 在缩放时调整波浪位置
    adjustWavePositionsOnResize() {
        if (!this.isUsingJSAnimation) return;
        
        // 获取两个波浪的当前位置
        const wave1Transform = getComputedStyle(this.waves[0]).transform;
        const wave2Transform = getComputedStyle(this.waves[1]).transform;
        
        let wave1X = 0;
        let wave2X = 0;
        
        // 解析transform值
        if (wave1Transform && wave1Transform !== 'none') {
            const matrix = wave1Transform.match(/matrix.*\((.+)\)/);
            if (matrix) {
                const values = matrix[1].split(', ');
                wave1X = parseFloat(values[4]) || 0;
            }
        }
        
        if (wave2Transform && wave2Transform !== 'none') {
            const matrix = wave2Transform.match(/matrix.*\((.+)\)/);
            if (matrix) {
                const values = matrix[1].split(', ');
                wave2X = parseFloat(values[4]) || 0;
            }
        }
        
        // 确定哪个波浪在左边，哪个在右边
        const leftWave = wave1X <= wave2X ? this.waves[0] : this.waves[1];
        const rightWave = wave1X <= wave2X ? this.waves[1] : this.waves[0];
        const leftX = Math.min(wave1X, wave2X);
        const rightX = Math.max(wave1X, wave2X);
        
        // 获取波浪长度
        const waveLength = this.waves[0].offsetWidth;
        
        // 将靠右的波浪移动到靠左波浪的尾部，使用requestAnimationFrame确保平滑
        const newRightX = leftX + waveLength;
        requestAnimationFrame(() => {
            rightWave.style.transform = `translateX(${newRightX}px)`;
        });
        
        console.log(`缩放时调整波浪位置: 左波浪=${leftX}px, 右波浪=${newRightX}px`);
    }

    // 使用ResizeObserver监测聊天框尺寸变化
    setupResizeObserver() {
        const chatBackground = document.getElementById('chat-background');
        if (chatBackground && window.ResizeObserver) {
            const resizeObserver = new ResizeObserver((entries) => {
                // 防抖处理，避免频繁更新
                if (this.resizeTimeout) {
                    clearTimeout(this.resizeTimeout);
                }
                
                this.resizeTimeout = setTimeout(() => {
                    this.recalculateWaveHeight();
                    this.adjustWavePositionsOnResize();
                }, 100); // 100ms防抖
            });
            
            resizeObserver.observe(chatBackground);
            console.log('ResizeObserver已设置，监测背景层尺寸变化');
        } else {
            // 降级方案：使用window resize事件
            window.addEventListener('resize', () => {
                if (this.resizeTimeout) {
                    clearTimeout(this.resizeTimeout);
                }
                
                this.resizeTimeout = setTimeout(() => {
                    this.recalculateWaveHeight();
                    this.adjustWavePositionsOnResize();
                }, 100);
            });
            console.log('使用window resize事件作为降级方案');
        }
    }
}

// 初始化波浪控制器
document.addEventListener('DOMContentLoaded', () => {
    window.waveController = new WaveController();
});

// 导出供其他脚本使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WaveController;
} 