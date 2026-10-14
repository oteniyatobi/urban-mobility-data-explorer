let paymentTypes = [];
let zones = [];
let currentPage = 1;
fetch('/api/payment_types')
    .then(response => response.json())
    .then(data => {
        paymentTypes = data;
    });
fetch('/api/zone')
    .then(response => response.json())
    .then(data => {
        zones = data;
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
    fetch(`/api/trip?page=${currentPage}`)
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