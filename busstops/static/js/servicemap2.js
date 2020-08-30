(function () {
    'use strict';

    /*jslint
        browser: true
    */
    /*global
        L, reqwest, loadjs
    */

    var container = document.getElementById('map'),
        service = container.getAttribute('data-service'),
        map,
        statusBar,
        bounds,
        // lastReq,
        // response,
        // oldVehicles = {},
        // newVehicles = {},
        busesOnline = document.getElementById('buses-online'),
        button = busesOnline.getElementsByTagName('a')[0];

    function setLocationHash(hash) {
        if (history.replaceState) {
            try {
                history.replaceState(null, null, location.pathname + hash);
            } catch (error) {
                // probably SecurityError (document is not fully active)
            }
        }
    }

    function openMap() {
        container.className += ' expanded';
        if (document.body.style.paddingTop) {
            container.style.top = document.body.style.paddingTop;
        }
        document.body.style.overflow = 'hidden';

        setLocationHash('#map');

        if (map) {
            map.invalidateSize();
        } else {
            loadjs([window.LEAFLET_CSS_URL, window.LEAFLET_JS_URL], setUpMap);
            // if (busesOnlineCount) {
            //     clearTimeout(timeout);
            //     load();
            // }
        }
    }

    button.onclick = openMap;

    function setUpMap() {
        map = L.map(container),
        map.attributionControl.setPrefix('');
        L.tileLayer('https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}{r}.png', {
            attribution: '<a href="https://stadiamaps.com/">© Stadia Maps</a> <a href="https://openmaptiles.org/">© OpenMapTiles</a> <a href="https://www.openstreetmap.org/about/">© OpenStreetMap contributors</a>',
        }).addTo(map);

        statusBar = L.control({
            position: 'bottomleft'
        });

        statusBar.onAdd = function() {
            var div = L.DomUtil.create('div', 'hugemap-status');
            return div;
        };

        statusBar.addTo(map);

        var closeButton = L.control();

        closeButton.onAdd = function() {
            var div = document.createElement('div');
            div.className = 'leaflet-bar';

            var a = document.createElement('a');
            a.href = '#';
            a.style.width = 'auto';
            a.style.padding = '0 8px';
            a.setAttribute('role', 'button');
            a.innerHTML = 'Close map';
            a.onclick = closeMap;

            div.appendChild(a);
            return div;
        };

        closeButton.addTo(map);

        if (window.EXTENT) {
            map.fitBounds([[window.EXTENT[1], window.EXTENT[0]], [window.EXTENT[3], window.EXTENT[2]]]);
        }

        reqwest('/services/' + service + '.json', function(data) {
            L.geoJson(data.geometry, {
                style: {
                    weight: 3,
                    color: '#87f'
                }
            }).addTo(map);
            var options = {
                radius: 3,
                fillColor: '#fff',
                color: '#87f',
                weight: 2,
                fillOpacity: 1
            };

            L.geoJson(data.stops, {
                pointToLayer: function (feature, latlng) {
                    return L.circleMarker(latlng, options).bindPopup('<a href="' + feature.properties.url + '">' + feature.properties.name + '</a>');
                }
            }).addTo(map);
        });

        // if (response) {
        //     processData(response);
        // }
    }

    function getTransform(heading, scale) {
        if (heading === null && !scale) {
            return '';
        }
        var transform = 'transform:';
        if (heading !== null) {
            transform += ' rotate(' + heading + 'deg)';
        }
        if (scale) {
            transform += ' scale(1.5)';
        }
        return '-webkit-' + transform + ';' + transform;
    }

    function getBusIcon(item, active) {
        var heading = item.h;
        if (heading !== null) {
            var arrow = '<div class="arrow" style="' + getTransform(heading, active) + '"></div>';
            if (heading < 180) {
                heading -= 90;
            } else {
                heading -= 270;
            }
        }
        var className = 'bus';
        if (active) {
            className += ' selected';
        }
        if (item.c) {
            var style = 'background:' + item.c;
            className += ' coloured';
            if (item.t) {
                className += ' white-text';
            }
            style += ';';
        } else {
            style = '';
        }
        style += getTransform(heading, active);
        var html = '<div class="' + className + '" style="' + style + '">';
        if (item.r) {
            html += item.r;
        }
        html += '</div>';
        if (arrow) {
            html += arrow;
        }
        return L.divIcon({
            iconSize: [20, 20],
            html: html,
            popupAnchor: [0, -5],
        });
    }

    var clickedMarker;

    function getPopupContent(item) {
        var delta = '';
        if (item.e === 0) {
            delta = 'On time<br>';
        } else if (item.e) {
            delta += 'About ';
            if (item.e > 0) {
                delta += item.e;
            } else {
                delta += item.e * -1;
            }
            delta += ' minute';
            if (item.e !== 1 && item.e !== -1) {
                delta += 's';
            }
            if (item.e > 0) {
                delta += ' early';
            } else {
                delta += ' late';
            }
            delta += '<br>';
        }

        var datetime = new Date(item.d);

        return delta + 'Updated at ' + datetime.toTimeString().slice(0, 5);
    }


    function handleMarkerClick(event) {
        if (clickedMarker) {
            // deselect previous clicked marker
            // (not always covered by popupclose handler, if popup hasn't opened yet)
            var marker = vehicles[clickedMarker];
            if (marker) {
                marker.setIcon(getBusIcon(marker.options.item));
            }
        }

        marker = event.target;
        var item = marker.options.item;

        clickedMarker = item.i;

        marker.setIcon(getBusIcon(item, true));

        var popup = marker.getPopup();
        if (!popup) {
            reqwest({
                url: '/vehicles/locations/' + clickedMarker,
                success: function(content) {
                    marker.options.popupContent = content;
                    marker.bindPopup(content + getPopupContent(item)).openPopup();
                },
                error: function() {
                    marker.options.popupContent = '';
                    marker.bindPopup(getPopupContent(item)).openPopup();
                }
            });

            marker.on('popupclose', function(event) {
                event.target.setIcon(getBusIcon(event.target.options.item));
                clickedMarker = null;
            });
        }
    }

    var vehicles = {};

    function handleVehicle(item) {
        var isClickedMarker = item.i === clickedMarker,
            icon = getBusIcon(item, isClickedMarker),
            latLng = L.latLng(item.l[1], item.l[0]);

        if (item.i in vehicles) {
            var marker = vehicles[item.i];
            marker.setLatLng(latLng);
            marker.setIcon(icon);
            marker.options.item = item;
            var popup = marker.getPopup();
            if (popup) {
                popup.setContent(marker.options.popupContent + getPopupContent(item));
            }
        } else {
            vehicles[item.i] = L.marker(latLng, {
                icon: icon,
                item: item,
                zIndexOffset: 1000
            }).addTo(map).on('click', handleMarkerClick);
        }
    }

    // function processData(data) {
    //     bounds = L.latLngBounds();

    //     for (var i = data.features.length - 1; i >= 0; i -= 1) {
    //         handleVehicle(data.features[i]);
    //     }
    //     for (var vehicle in oldVehicles) {
    //         if (!(vehicle in newVehicles)) {
    //             map.removeLayer(oldVehicles[vehicle]);
    //         }
    //     }
    //     oldVehicles = newVehicles;
    //     newVehicles = {};

    //     if (!map._loaded && bounds.isValid()) {
    //         map.fitBounds(bounds, {
    //             padding: [10, 10],
    //             maxZoom: 12
    //         });
    //     }
    //     statusBar.getContainer().innerHTML = '';
    // }

    var timeout, busesOnlineCount;

    // websocket

    var socket,
        backoff = 1000,
        newSocket;

    var first = false;

    function connect() {
        if (socket && socket.readyState < 2) { // already CONNECTING or OPEN
            return; // no need to reconnect
        }
        var url = (window.location.protocol === 'http:' ? 'ws' : 'wss') + '://' + window.location.host + '/ws/vehicle_positions/services/' + service;
        socket = new WebSocket(url);

        socket.onopen = function() {
            backoff = 1000;
            newSocket = true;

            // var bounds = map.getBounds();
            // socket.send(JSON.stringify([
            //     bounds.getWest(),
            //     bounds.getSouth(),
            //     bounds.getEast(),
            //     bounds.getNorth()
            // ]));
        };

        socket.onclose = function() {
            window.setTimeout(connect, backoff);
            backoff += 500;
        };

        socket.onerror = function(event) {
            console.error(event);
        };

        socket.onmessage = function(event) {
            var items = JSON.parse(event.data);

            if (!busesOnlineCount) { // first load
                if (items.length) {
                    busesOnlineCount = document.createElement('span');
                    busesOnline.appendChild(busesOnlineCount);
                    if (items.length === 1) {
                        busesOnlineCount.innerHTML = 'Tracking 1 bus';
                    } else {
                        busesOnlineCount.innerHTML = 'Tracking ' + items.length + ' buses';
                    }
                } else {
                    return;
                }
            }



            if (newSocket && !first) {
                var newVehicles = {};
            }
            newSocket = false;
            for (var i = items.length - 1; i >= 0; i--) {
                handleVehicle(items[i]);
                if (newVehicles) {
                    newVehicles[items[i].i] = true;
                }
            }
            if (newVehicles) {
                for (var id in vehicles) {
                    if (!(id in newVehicles)) {
                        map.removeLayer(vehicles[id]);
                        delete vehicles[id];
                    }
                }
            }
        };
    }

        // if (statusBar) {
        //     statusBar.getContainer().innerHTML = 'Loading\u2026';
        // }
        // if (lastReq) {
        //     lastReq.abort();
        // }
        // lastReq = reqwest('/vehicles.json?service=' + service, function(data) {
        //     if (lastReq.request.status === 200 && data && data.features) {
        //         if (!busesOnlineCount) { // first load
        //             if (data.features.length) {
        //                 busesOnlineCount = document.createElement('span');
        //                 busesOnline.appendChild(busesOnlineCount);
        //                 if (document.addEventListener) {
        //                     document.addEventListener('visibilitychange', handleVisibilityChange);
        //                 }
        //             } else {
        //                 if (statusBar) {
        //                     statusBar.getContainer().innerHTML = '';
        //                 }
        //                 return;
        //             }
        //         }

        //         if (data.features.length === 0) {
        //             busesOnlineCount.innerHTML = '';
        //         } else if (data.features.length === 1) {
        //             busesOnlineCount.innerHTML = 'Tracking 1 bus';
        //         } else {
        //             busesOnlineCount.innerHTML = 'Tracking ' + data.features.length + ' buses';
        //         }
        //         if (map) {
        //             processData(data);
        //         } else {
        //             response = data;
        //         }
        //     }
        //     timeout = setTimeout(function() {
        //         load();
        //     }, map ? 10000 : 120000); // 10 seconds or 2 minute
        // });
    // }

    // function handleVisibilityChange(event) {
    //     if (event.target.hidden) {
    //         clearTimeout(timeout);
    //     } else {
    //         load();
    //     }
    // }

    function closeMap() {
        container.className = container.className.replace(' expanded', '');
        document.body.style.overflow = '';
        setLocationHash('');

        return false;
    }

    window.onkeydown = function(event) {
        if (event.keyCode === 27) {
            closeMap();
        }
    };

    window.onhashchange = function(event) {
        if (event.target.location.hash === '#map') {
            openMap();
        } else {
            closeMap();
        }
    };

    connect();
    if (window.location.hash === '#map') {
        openMap();
    }

})();
