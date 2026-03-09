// Initialize Chart
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();
        
        const ctx = document.getElementById('degradationChart').getContext('2d');
        
        // Gradient for predicted area
        let gradientPredict = ctx.createLinearGradient(0, 0, 0, 400);
        gradientPredict.addColorStop(0, 'rgba(245, 158, 11, 0.2)');
        gradientPredict.addColorStop(1, 'rgba(245, 158, 11, 0.0)');

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: 'Historical Capacity',
                        data: data.datasets[0].data,
                        borderColor: '#10b981',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.4
                    },
                    {
                        label: 'Predicted Degradation',
                        data: data.datasets[1].data,
                        borderColor: '#f59e0b',
                        backgroundColor: gradientPredict,
                        borderWidth: 2,
                        borderDash: [5, 5],
                        fill: true,
                        pointRadius: 0,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: '#1e293b',
                        titleColor: '#f8fafc',
                        bodyColor: '#cbd5e1',
                        borderColor: '#334155',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: '#64748b', maxTicksLimit: 8 }
                    },
                    y: {
                        grid: { color: '#334155', borderDash: [2, 4] },
                        ticks: { color: '#64748b' }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
        
    } catch (error) {
        console.error("Error loading chart data:", error);
    }
});
