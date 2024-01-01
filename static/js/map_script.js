// Create list of timestamps to compare with data coming from database
let timestamps = [];
document.addEventListener("DOMContentLoaded", function() {
    timestamps.length = 0;
    let currentTime = new Date();
    currentTime.setTime(currentTime.getTime() + 2 * 60 * 60 * 1000);
    const options = { timeZone: 'Europe/Helsinki' };
    for (let i = 0; i < 7; i++) {
        const formattedTimestamp = currentTime.toISOString(options).replace('T', ' ').slice(0, 19);
        timestamps.push(formattedTimestamp);
        currentTime.setMinutes(currentTime.getMinutes() - 10);
    }
});


// Function to fetch data asynchronously
function fetchDataAndInitializeMap() {
    $.ajax({
        url: '/get_coordinates_data',
        type: 'GET',
        dataType: 'json',
        success: function (data) {
            var coordinates = data;

            // Fetch traffic data
            $.ajax({
                url: '/get_traffic_data',
                type: 'GET',
                dataType: 'json',
                success: function (trafficData) {
                    var traffic_data = trafficData;
                    initializeMap(coordinates, traffic_data);
                },
                error: function (error) {
                    console.error('Error fetching traffic data:', error);
                    showError('Failed to fetch traffic data. Please try again later.');
                }
            });
        },
        error: function (error) {
            console.error('Error fetching coordinates data:', error);
            showError('Failed to fetch coordinates data. Please try again later.');
        }
    });
}

// Function to display error messages to the user
function showError(message) {
    alert('Error: ' + message);
}

// Function to initialize the map with the provided data
function initializeMap(coordinates, traffic_data) {
    $(function () {
        // Initialize the map
        var map = L.map('map').setView([61.497118, 23.765519], 14);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

        var timestampKeys = Object.keys(traffic_data);
        var lastTimestampIndex = timestampKeys.length - 1;
        var selectedTimestampKey = timestampKeys[lastTimestampIndex];
        var selectedTimestampData = traffic_data[selectedTimestampKey];

        addMarkers(selectedTimestampData, coordinates, selectedTimestampKey, map, 0);

        // Initialize the slider
        var slider = $("#time-slider").slider({
            min: -60,   // -60 minutes
            max: 60,    // 60 minutes
            value: 0,   // Initial value (live)
            step: 10,   // 10-minute steps
            slide: function (event, ui) {
                if (!timestampKeys) {
                    console.error("Timestamp keys are not defined.");
                    return;
                }

                // Calculate the selected timestamp index based on the slider value
                var selectedTimestampIndex = Math.floor(ui.value / 10) + 6;

                // Ensure the index is within bounds
                selectedTimestampIndex = Math.max(0, Math.min(timestampKeys.length - 1, selectedTimestampIndex));

                var selectedTimestampKey = timestampKeys[selectedTimestampIndex];
                updateMapWithSelectedTimestamp(selectedTimestampKey, ui.value);
                updateTimeIndicator(ui.value);
            }
        });

        // Reset button click event
        $("#reset-button").on("click", function () {
            slider.slider("value", 0);
            resetMapData(timestampKeys, coordinates, traffic_data);
            updateTimeIndicator(0);
        });

        // Function to update the map with the data for the selected timestamp
        function updateMapWithSelectedTimestamp(selectedTimestampKey, timeIndex) {
            var selectedTimestampData = traffic_data[selectedTimestampKey];

            map.eachLayer(function (layer) {
                if (layer instanceof L.CircleMarker) {
                    map.removeLayer(layer);
                }
            });

            addMarkers(selectedTimestampData, coordinates, selectedTimestampKey, map, timeIndex);
        }

        // Function to update the time indicator
        function updateTimeIndicator(minutes) {
            if (minutes === 0) {
                $("#time-indicator").text("Live");
            } else if (minutes < 0) {
                $("#time-indicator").text(minutes + " minutes ago");
            } else {
                $("#time-indicator").text("+" + minutes + " minutes");
            }
        }

        // Function to reset the map data
        function resetMapData() {
            // Clear existing markers
            map.eachLayer(function (layer) {
                if (layer instanceof L.CircleMarker) {
                    map.removeLayer(layer);
                }
            });

            // Choose latest timestamp
            var lastTimestampIndex = timestampKeys.length - 1;
            var selectedTimestampKey = timestampKeys[lastTimestampIndex];
            var selectedTimestampData = traffic_data[selectedTimestampKey];

            // Add markers
            addMarkers(selectedTimestampData, coordinates, selectedTimestampKey, map, 0);
        }
    });
}

function addMarkers(selectedTimestampData, coordinates, selectedTimestampKey, map, timeIndex) {
    for (var deviceKey in selectedTimestampData) {
        if (selectedTimestampData.hasOwnProperty(deviceKey)) {
            var trafficAmount = selectedTimestampData[deviceKey];
            var deviceCoordinates = coordinates[deviceKey];

            // Check if the device key is in coordinates
            if (deviceCoordinates) {
                var coord = [deviceCoordinates[0][1], deviceCoordinates[0][0]];

                // Set the color of the marker based on the traffic amount
                var dynamicColor = calculateColor(trafficAmount);
                var showWhenDataFteched = selectedTimestampKey;
                var showTrafficAmount = trafficAmount;

                const date1 = new Date(selectedTimestampKey);
                const date2 = new Date(timestamps[timeIndex]);
                if(Math.abs(date1-date2)>600000) {
                    var showWhenDataFteched = "No data from this time. Try reloading the page.";
                    var showTrafficAmount = "No data from this time. Try reloading the page.";
                    dynamicColor = "#000000";
                }

                L.circle(coord, {
                    color: dynamicColor,
                    fillColor: dynamicColor,
                    fillOpacity: 0.8,
                    radius: 60
                }).addTo(map).bindPopup('ID: ' + deviceKey + '<br>Cars in the last hour: ' + showTrafficAmount
                    + '<br>Data fetched at: ' + showWhenDataFteched);
            }
        }
    }
}

function calculateColor(trafficAmount) {
    if (trafficAmount >= 2000) {
        return "#FF0000";
    } else {
        // Normalize traffic amount to a value between 0 and 1
        var normalizedValue = trafficAmount / 2000;

        // Interpolate color between green and red
        var red = Math.floor(255 * normalizedValue);
        var green = Math.floor(255 * (1 - normalizedValue));
        var blue = 0;

        // Convert RGB values to hexadecimal color code
        return rgbToHex(red, green, blue);
    }
}

function rgbToHex(r, g, b) {
    var componentToHex = function (c) {
        var hex = c.toString(16);
        return hex.length == 1 ? "0" + hex : hex;
    };
    return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
}

// Call the function to fetch data and initialize the map
fetchDataAndInitializeMap();
