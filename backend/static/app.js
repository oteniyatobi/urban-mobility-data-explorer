let paymentTypes = [];
let zones = [];
let currentPage = 1;
let currentTrips = [];
let sortColumn = null;
let sortDir = 'asc';


fetch('/api/payment_types')
    .then(response => response.json())
    .then(data => {
        paymentTypes = data;
    data.forEach(trip => {
        const option = document.createElement('option');
        option.value = trip.payment_type_id;
        option.textContent = trip.description;
        document.getElementById('paymentType').appendChild(option);
    });
});

fetch('/api/zone')
    .then(response => response.json())
    .then(data => {
        zones = data;
    data.forEach(zone => {
        const option = document.createElement('option');
        option.value = zone.location_id;
        option.textContent = zone.zone_name;
        document.getElementById('pickupZone').appendChild(option);
    });
});

function showTripDetails(tripId) {
    fetch(`/api/trip?trip_id=${tripId}`)
        .then(response => response.json())
        .then(data => {
             const trip = data[0]
            if (!trip) return
            const detailList = document.getElementById('detailList');
            detailList.innerHTML = '';
            for (const [key, value] of Object.entries(trip)) {
                const dt = document.createElement('dt');
                dt.textContent = key;
                const dd = document.createElement('dd');
                dd.textContent = value;
                detailList.appendChild(dt);
                detailList.appendChild(dd);
            }
            document.getElementById('detailBox').showModal();
        });
}

document.getElementById('applyButton').addEventListener('click', () => {
    currentPage = 1;
    document.getElementById('pageLabel').textContent = 'Page 1';
    loadTrips();
});
document.getElementById('resetButton').addEventListener('click', () => {
    document.getElementById('dateFrom').value = '';
    document.getElementById('dateTo').value = '';
    document.getElementById('paymentType').value = '';
    document.getElementById('pickupZone').value = '';
    currentPage = 1;
    document.getElementById('pageLabel').textContent = 'Page 1';
    loadTrips();
   
});

document.getElementById('nextButton').addEventListener('click', () => {
    currentPage++;
    document.getElementById('pageLabel').textContent = 'Page ' + currentPage;
    loadTrips();
})
document.getElementById('prevButton').addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage--;
        document.getElementById('pageLabel').textContent = 'Page ' + currentPage;
        loadTrips();
    }
});

function loadTrips(){
    const dateFrom = document.getElementById('dateFrom').value;
    const dateTo = document.getElementById('dateTo').value;
    const limit = document.getElementById('pageSize').value;
    const paymentType = document.getElementById('paymentType').value;
    const pickupZone = document.getElementById('pickupZone').value;  
    let url = `/api/trip?page=${currentPage}&limit=${limit}`;
    if (dateFrom) url += `&date_from=${dateFrom}`;
    if (dateTo) url += `&date_to=${dateTo}`;
    if (paymentType) url += `&payment_type=${paymentType}`;
    if (pickupZone) url += `&pickup_location_id=${pickupZone}`;
    fetch(url)

        .then(response => response.json())
        .then(data => {
            currentTrips = Array.isArray(data) ? data : [];
            renderTripTable();
            renderDistanceChart();
        });
    }

function renderTripTable() {
    const tripBody = document.getElementById('tripBody');
    tripBody.innerHTML = '';

    if (currentTrips.length === 0) {
        tripBody.innerHTML = '<tr><td colspan="9" style="text-align:center"> No trips match the filters</td></tr>';
        return;
    }

    currentTrips.forEach(trip => {
        const tripRow = document.createElement('tr');
        tripRow.innerHTML = `
                    <td>${trip.trip_id}</td>
                    <td>${trip.pickup_datetime}</td>
                    <td>${trip.dropoff_datetime}</td>
                    <td>${Number(trip.trip_distance).toFixed(2)}</td>
                    <td>${paymentTypes.find(p => p.payment_type_id === trip.payment_type_id)?.description || trip.payment_type_id}</td>
                    <td>${trip.passenger_count}</td>
                    <td>${zones.find(z => z.location_id === trip.pickup_location_id)?.zone_name || trip.pickup_location_id}</td>
                    <td>${zones.find(z => z.location_id === trip.dropoff_location_id)?.zone_name || trip.dropoff_location_id}</td>
                    <td><button class="button button-main" onclick="showTripDetails(${trip.trip_id})">Details</button></td>
                `;
                tripBody.appendChild(tripRow);
            });
    }




loadTrips();
document.getElementById('closeDetail').addEventListener('click', () => {
    document.getElementById('detailBox').close()
})

async function loadCharts() {

    try {
        const resp = await fetch('/api/stats/hourly');
        const data = await resp.json();

        const weekday = data.filter(d => d.is_weekend === 0).sort((a, b) => a.pickup_hour - b.pickup_hour)
        const weekend = data.filter(d => d.is_weekend === 1).sort((a, b) => a.pickup_hour - b.pickup_hour)
        const labels = Array.from({ length: 24 }, (_, i) => `${i}:00`);

        new Chart(document.getElementById('hourChart'), {
            type: 'line',
            data: {
                labels,
                datasets: [
                    { label: 'Weekday', data: weekday.map(d => d.trips), borderColor: '#2b5fa8', backgroundColor: 'rgba(43,95,168,0.15)', tension: 0.3, fill: true},
                    { label: 'Weekend', data: weekend.map(d => d.trips), borderColor: '#ffc20e', backgroundColor: 'rgba(255,194,14,0.15)', tension: 0.3, fill: true},
                ],
            },
            options: { responsive: true, maintainAspectRatio: false},
        });
    } catch (err) { console.error('hourly chart failed', err);}


    try {
        const resp = await fetch('/api/stats/payments')
        const data = await resp.json();

        new Chart(document.getElementById('paymentChart'),{
            type: 'doughnut',
            data: {
                labels: data.map(d => d.payment_type),
                datasets: [{
                    data: data.map(d => d.trips),
                    backgroundColor: ['#2b5fa8', '#ffc20e', '#5b6168', '#23272b', '#8aa9d4', '#e6ad00'],
                }],
            },
            options: { responsive: true, maintainAspectRatio: false},
        });
    } catch (err) {console.error('payment chart failed', err); }

    //zones

    try {
        const resp = await fetch('/api/stats/top-zones?k=5');
        const data = await resp.json();
        const list = document.getElementById('topZones');
        list.innerHTML = '';
        data.forEach(z => {
            const li = document.createElement('li');
            li.innerHTML = `<strong>${z.zone_name}</strong> <span styles=color:#5b6168">(${z.borough})</span> - ${z.pickups.toLocaleString()} pickups`;
            list.appendChild(li);
        });
    } catch (err) { console.error('top zones failed', err); }
    
}

function renderDistanceChart() {
    const groups = { '<1 mi': 0, '1-3 mi': 0, '3-10 mi': 0, '10+ mi': 0};
    currentTrips.forEach(t => {
        const d = Number(t.trip_distance);
        if (d < 1) groups['<1 mi']++;
        else if (d < 3) groups['1-3 mi']++;
        else if (d < 10) groups['3-10 mi']++;
        else groups['10+ mi']++;
    });

    const existing = Chart.getChart('distanceChart');
    if (existing) existing.destroy();

    new Chart(document.getElementById('distanceChart'), {
        type: 'bar',
        data: {
            labels: Object.keys(groups),
            datasets: [{ label: 'Trips on this page', data:Object.values(groups), backgroundColor: '#2b5fa8'}],
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: {legend: {display: false }}},
    });
}


function applyLocalFiltersAndSort() {
    const minDist = parseFloat(document.getElementById('minDistance')?.value) || null;
    const maxDist = parseFloat(document.getElementById('maxDistance')?.value) || null;
    const minFare = parseFloat(document.getElementById('minFare')?.value) || null;
    const maxFare = parseFloat(document.getElementById('maxFare')?.value) || null;
    const pickupZone = document.getElementById('pickupZone').value;


    currentTrips = currentTrips.filter(t => {
        if (minDist !== null && t.trip_distance < minDist) return false;
        if (maxDist !== null && t.trip_distance > maxDist) return false;
        if (minFare !== null && t.total_amount < minFare) return false;
        if (maxFare !== null && t.total_amount > maxFare) return false;

        return true;
    });

    if (sortColumn) {
        currentTrips.sort((a, b) => {
            const av = a[sortColumn];
            const bv = b[sortColumn];

            if (av === bv) return 0;
            return (av > bv ? 1 : -1) * (sortDir === 'asc' ? 1 : -1);
        });
    }
}

//column sort


document.querySelectorAll('#tripHead th').forEach(th => {
    th.addEventListener('click', () => {
        const label = th.textContent.trim().toLowerCase();
        const map = {
            'id': 'trip_id',
            'pickup': 'pickup_datetime',
            'dropoff': 'dropoff_datetime',
            'distance': 'trip_distance',
            'passengers': 'passenger_count',
        };

        const col = map[label];
        if (!col) return;
        if (sortColumn === col) {
            sortDir = sortDir === 'asc' ? 'desc' : 'asc';
        } else {
            sortColumn = col;
            sortDir = 'asc';
        }

        applyLocalFiltersAndSort();
        renderTripTable();
    });
});


loadCharts();