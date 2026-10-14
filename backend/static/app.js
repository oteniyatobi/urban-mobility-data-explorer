let paymentTypes = [];
let zones = [];
let currentPage = 1;
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
            const tripBody = document.getElementById('tripBody');
            tripBody.innerHTML = '';
            data.forEach(trip => {
                const tripRow = document.createElement('tr');
                tripRow.innerHTML = `
                    <td>${trip.trip_id}</td>
                    <td>${trip.pickup_datetime}</td>
                    <td>${trip.dropoff_datetime}</td>
                    <td>${trip.trip_distance}</td>
                    <td>${paymentTypes.find(p => p.payment_type_id === trip.payment_type_id)?.description || trip.payment_type_id}</td>
                    <td>${trip.passenger_count}</td>
                    <td>${zones.find(z => z.location_id === trip.pickup_location_id)?.zone_name || trip.pickup_location_id}</td>
                    <td>${zones.find(z => z.location_id === trip.dropoff_location_id)?.zone_name || trip.dropoff_location_id}</td>
                    <td><button class="button button-main" onclick="showTripDetails(${trip.trip_id})">Details</button></td>
                `;
                tripBody.appendChild(tripRow);
            });
        });
}
loadTrips();
document.getElementById('closeDetail').addEventListener('click', () => {
    document.getElementById('detailBox').close()
})