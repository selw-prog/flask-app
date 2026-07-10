let tornadoChart = null;

document.getElementById('loadBtn').addEventListener('click', loadEvents);

function loadEvents() {
    const state = document.getElementById('stateSelect').value;
    if (!state) return;

    fetch(`/projects/tornado/api/events?state=${encodeURIComponent(state)}`)
        .then(r => r.json())
        .then(data => {
            document.getElementById('results').classList.add('d-none');
            document.getElementById('emptyState').classList.add('d-none');

            if (data.length === 0) {
                document.getElementById('emptyState').classList.remove('d-none');
                return;
            }

            renderTable(data);
            renderChart(data);
            document.getElementById('results').classList.remove('d-none');
        })
        .catch(err => console.error('Failed to load events:', err));
}

function renderTable(events) {
    const tbody = document.getElementById('eventsBody');
    tbody.innerHTML = '';
    events.forEach(e => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${e.event_date}</td>
            <td>${e.county}</td>
            <td>${e.location ?? '—'}</td>
            <td><span class="badge bg-secondary">${e.scale ?? 'N/A'}</span></td>
        `;
        tbody.appendChild(row);
    });
}

function renderChart(events) {
    const countsByYear = {};
    events.forEach(e => {
        const year = e.event_date.substring(0, 4);
        countsByYear[year] = (countsByYear[year] ?? 0) + 1;
    });

    const labels = Object.keys(countsByYear).sort();
    const counts = labels.map(y => countsByYear[y]);
    const avg = counts.reduce((a, b) => a + b, 0) / counts.length;

    if (tornadoChart) tornadoChart.destroy();

    tornadoChart = new Chart(document.getElementById('tornadoChart'), {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Tornado Events',
                data: counts,
                backgroundColor: 'rgba(13, 110, 253, 0.6)',
                borderColor: 'rgba(13, 110, 253, 1)',
                borderWidth: 1,
            }]
        },
        options: {
            responsive: true,
            plugins: {
                annotation: {
                    annotations: {
                        avgLine: {
                            type: 'line',
                            yMin: avg,
                            yMax: avg,
                            borderColor: 'rgba(255, 193, 7, 0.8)',
                            borderWidth: 2,
                            borderDash: [6, 4],
                            label: {
                                display: true,
                                content: `Avg: ${avg.toFixed(1)}`,
                                position: 'end',
                            }
                        }
                    }
                }
            },
            scales: {
                y: { beginAtZero: true, ticks: { color: '#adb5bd' }, grid: { color: '#2d2d2d' } },
                x: { ticks: { color: '#adb5bd' }, grid: { color: '#2d2d2d' } },
            }
        }
    });
}
