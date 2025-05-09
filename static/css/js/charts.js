function createChart(timestamps, gasData, tempData, humidityData) {
    const ctx = document.getElementById('sensorChart').getContext('2d');
    
    // Convertir timestamps a formato legible
    const labels = timestamps.map(timestamp => {
        const date = new Date(timestamp);
        return date.toLocaleTimeString();
    });
    
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Nivel de Gas',
                    data: gasData,
                    borderColor: '#f57c00',
                    backgroundColor: 'rgba(245, 124, 0, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y-gas',
                },
                {
                    label: 'Temperatura (°C)',
                    data: tempData,
                    borderColor: '#f44336',
                    backgroundColor: 'rgba(244, 67, 54, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y-temp',
                },
                {
                    label: 'Humedad (%)',
                    data: humidityData,
                    borderColor: '#2196f3',
                    backgroundColor: 'rgba(33, 150, 243, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y-humidity',
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Histórico de Sensores',
                    color: 'white',
                    font: {
                        size: 16
                    }
                },
                legend: {
                    labels: {
                        color: 'white'
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                'y-gas': {
                    type: 'linear',
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Nivel de Gas',
                        color: '#f57c00'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                'y-temp': {
                    type: 'linear',
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Temperatura (°C)',
                        color: '#f44336'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    },
                    grid: {
                        display: false
                    }
                },
                'y-humidity': {
                    type: 'linear',
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Humedad (%)',
                        color: '#2196f3'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}