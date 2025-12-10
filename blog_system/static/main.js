// 主JavaScript文件 - 博客系统前端交互逻辑

document.addEventListener('DOMContentLoaded', function() {
    // 初始化所有功能
    initLikeSystem();
    initCommentSystem();
    initSearchSystem();
    initNetworkMonitor();
    initFormValidation();
    initResponsiveMenu();
});

// 点赞系统
function initLikeSystem() {
    // 全局点赞功能
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('like-btn') || e.target.closest('.like-btn')) {
            const btn = e.target.classList.contains('like-btn') ? e.target : e.target.closest('.like-btn');
            const articleId = btn.getAttribute('data-article-id') || 
                            btn.id.replace('like-btn-', '');
            
            if (articleId) {
                likeArticle(parseInt(articleId), btn);
            }
        }
    });
}

// 点赞文章函数
function likeArticle(articleId, button) {
    // 显示加载状态
    const originalText = button.innerHTML;
    button.innerHTML = '<span class="loading"></span>';
    button.disabled = true;
    
    fetch('/like', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `article_id=${articleId}`
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('网络响应不正常');
        }
        return response.json();
    })
    .then(data => {
        // 更新点赞计数
        const likeCountElement = document.getElementById(`like-count-${articleId}`);
        if (likeCountElement) {
            likeCountElement.textContent = data.like_count;
        }
        
        // 更新按钮状态
        if (data.action === 'like') {
            button.classList.add('liked');
            button.innerHTML = '👍 已点赞';
        } else {
            button.classList.remove('liked');
            button.innerHTML = '👍 点赞';
        }
        
        // 显示成功消息
        showToast(data.action === 'like' ? '点赞成功！' : '取消点赞');
    })
    .catch(error => {
        console.error('点赞错误:', error);
        button.innerHTML = originalText;
        showToast('操作失败，请重试', 'error');
    })
    .finally(() => {
        button.disabled = false;
    });
}

// 评论系统
function initCommentSystem() {
    // 回复按钮点击事件
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('reply-btn') || e.target.closest('.reply-btn')) {
            const btn = e.target.classList.contains('reply-btn') ? e.target : e.target.closest('.reply-btn');
            toggleReplyForm(btn);
        }
        
        // 取消回复
        if (e.target.classList.contains('cancel-reply') || e.target.closest('.cancel-reply')) {
            const btn = e.target.classList.contains('cancel-reply') ? e.target : e.target.closest('.cancel-reply');
            const replyForm = btn.closest('.reply-form');
            replyForm.style.display = 'none';
        }
    });
    
    // 评论表单提交
    document.addEventListener('submit', function(e) {
        if (e.target.matches('form[action*="/comment"]')) {
            e.preventDefault();
            submitCommentForm(e.target);
        }
    });
}

// 切换回复表单显示
function toggleReplyForm(button) {
    const commentElement = button.closest('.comment');
    const replyForm = commentElement.querySelector('.reply-form');
    
    if (replyForm) {
        const isVisible = replyForm.style.display === 'block';
        replyForm.style.display = isVisible ? 'none' : 'block';
        
        // 自动聚焦到文本域
        if (!isVisible) {
            const textarea = replyForm.querySelector('textarea');
            if (textarea) {
                textarea.focus();
            }
        }
    }
}

// 提交评论表单
function submitCommentForm(form) {
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    // 显示加载状态
    submitBtn.innerHTML = '<span class="loading"></span> 提交中...';
    submitBtn.disabled = true;
    
    fetch(form.action, {
        method: 'POST',
        body: new FormData(form)
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
            return;
        }
        return response.text();
    })
    .then(() => {
        // 页面会重定向，所以这里不需要额外处理
    })
    .catch(error => {
        console.error('评论提交错误:', error);
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
        showToast('评论提交失败，请重试', 'error');
    });
}

// 搜索系统
function initSearchSystem() {
    const searchForm = document.querySelector('.search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const input = this.querySelector('input[name="q"]');
            if (!input.value.trim()) {
                e.preventDefault();
                showToast('请输入搜索关键词', 'warning');
                input.focus();
            }
        });
    }
    
    // 实时搜索建议（可选功能）
    const searchInput = document.querySelector('input[name="q"]');
    if (searchInput) {
        let timeoutId;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                if (this.value.length > 2) {
                    // 这里可以添加实时搜索建议的API调用
                    // fetchSearchSuggestions(this.value);
                }
            }, 500);
        });
    }
}

// 网络监控系统
function initNetworkMonitor() {
    // 只在网络监控页面初始化图表
    if (document.getElementById('networkChart')) {
        initNetworkChart();
        startNetworkMonitoring();
    }
    
    // 全局网络状态显示
    const networkStatsElement = document.getElementById('network-stats');
    if (networkStatsElement) {
        updateGlobalNetworkStats();
        setInterval(updateGlobalNetworkStats, 5000);
    }
}

// 初始化网络监控图表
function initNetworkChart() {
    const ctx = document.getElementById('networkChart').getContext('2d');
    window.networkChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: '延迟 (ms)',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: '吞吐量 (req/min)',
                    data: [],
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: '网络性能监控'
                }
            }
        }
    });
}

// 开始网络监控
function startNetworkMonitoring() {
    updateNetworkStats();
    setInterval(updateNetworkStats, 3000);
}

// 更新网络统计数据
function updateNetworkStats() {
    fetch('/api/network/current')
        .then(response => response.json())
        .then(data => {
            // 更新当前统计显示
            document.getElementById('current-latency').textContent = data.latency.toFixed(1) + ' ms';
            document.getElementById('current-throughput').textContent = data.throughput + ' req/min';
            document.getElementById('current-connections').textContent = data.active_connections;
            
            // 更新图表
            if (window.networkChart) {
                const now = new Date().toLocaleTimeString();
                
                if (window.networkChart.data.labels.length > 20) {
                    window.networkChart.data.labels.shift();
                    window.networkChart.data.datasets[0].data.shift();
                    window.networkChart.data.datasets[1].data.shift();
                }
                
                window.networkChart.data.labels.push(now);
                window.networkChart.data.datasets[0].data.push(data.latency);
                window.networkChart.data.datasets[1].data.push(data.throughput);
                
                window.networkChart.update();
            }
        })
        .catch(error => {
            console.error('网络监控数据获取失败:', error);
        });
}

// 更新全局网络状态显示
function updateGlobalNetworkStats() {
    const element = document.getElementById('network-stats');
    if (!element) return;
    
    fetch('/api/network/current')
        .then(response => response.json())
        .then(data => {
            element.innerHTML = `
                <small class="text-muted">
                    延迟: ${data.latency.toFixed(1)}ms | 
                    吞吐量: ${data.throughput} req/min | 
                    连接数: ${data.active_connections}
                </small>
            `;
        });
}

// 表单验证系统
function initFormValidation() {
    const forms = document.querySelectorAll('form[needs-validation]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
                
                // 显示验证错误
                const invalidFields = form.querySelectorAll(':invalid');
                if (invalidFields.length > 0) {
                    invalidFields[0].focus();
                    showToast('请填写所有必填字段', 'warning');
                }
            }
            
            form.classList.add('was-validated');
        });
    });
}

// 响应式菜单
function initResponsiveMenu() {
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
        navbarToggler.addEventListener('click', function() {
            navbarCollapse.classList.toggle('show');
        });
        
        // 点击菜单外区域关闭菜单
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.navbar') && navbarCollapse.classList.contains('show')) {
                navbarCollapse.classList.remove('show');
            }
        });
    }
}

// 显示Toast通知
function showToast(message, type = 'success') {
    // 移除现有的toast
    const existingToasts = document.querySelectorAll('.custom-toast');
    existingToasts.forEach(toast => toast.remove());
    
    const toast = document.createElement('div');
    toast.className = `custom-toast alert alert-${type} alert-dismissible fade show`;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
    `;
    
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(toast);
    
    // 3秒后自动消失
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 3000);
}

// 工具函数：防抖
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 工具函数：节流
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 图片懒加载
function initLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.getAttribute('data-src');
                img.classList.remove('lazy');
                observer.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// 键盘快捷键
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K 聚焦搜索框
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('input[name="q"]');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // ESC键关闭所有模态框和下拉菜单
    if (e.key === 'Escape') {
        const openModals = document.querySelectorAll('.modal.show');
        openModals.forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        });
        
        const openDropdowns = document.querySelectorAll('.dropdown-menu.show');
        openDropdowns.forEach(dropdown => {
            dropdown.classList.remove('show');
        });
    }
});

// 页面性能监控
if ('performance' in window) {
    window.addEventListener('load', function() {
        const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
        console.log('页面加载时间:', loadTime + 'ms');
        
        // 可以发送到统计服务
        // sendMetrics({ loadTime: loadTime });
    });
}

// 错误监控
window.addEventListener('error', function(e) {
    console.error('JavaScript错误:', e.error);
    // 可以发送错误信息到服务器
    // sendErrorToServer(e.error);
});

// 导出全局函数
window.likeArticle = likeArticle;
window.showToast = showToast;