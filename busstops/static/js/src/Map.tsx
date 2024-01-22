import React, { memo } from "react";
import { createRoot } from "react-dom/client";
// import { captureException } from "@sentry/react";

import Map, {
  NavigationControl,
  GeolocateControl,
  MapEvent,
  AttributionControl,
  useControl
} from "react-map-gl/maplibre";

import stopMarker from "data-url:../../stop-marker.png";
import routeStopMarker from "data-url:../../route-stop-marker.png";
import arrow from "data-url:../../arrow.png";

const images: { [imageName: string]: string } = {
  "stop-marker": stopMarker,
  "route-stop-marker": routeStopMarker,
  arrow: arrow,
};

const mapStyles = [
  ["alidade_smooth", "Default"],
  ["osm_bright", "Bright"],
  ["outdoors", "Outdoors"],
  // ["alidade_satellite", "Satellite"],
];

class StyleSwitcher {
  constructor(props) {
    this.style = props.style;
    this.handleChange = props.onChange;
  }

  onAdd(map) {
    this._map = map;
    this._container = document.createElement('div');

    let root = createRoot(this._container);
    root.render(
      <details className="maplibregl-ctrl maplibregl-ctrl-group map-style-switcher">
        <summary className="maplibregl-ctrl-icon">Map style</summary>
        {mapStyles.map(style => {
          let [key, value] = style;
          return <label key={key}><input type="radio" value={key} name="map-style" defaultChecked={key === this.style} onChange={this.handleChange} />{value}</label>;
        })}
      </details>
    );
    return this._container;
  }

  onRemove() {
    this._container.parentNode.removeChild(this._container);
    this._map = undefined;
  }
}

const StyleSwitcherControl = memo(function(props) {
  useControl(() => new StyleSwitcher(props));

  return null;
});

export default function BusTimesMap(props: any) {
  const imageNames = props.images;
  const onLoad = props.onLoad;

  const [mapStyle, setMapStyle] = React.useState("alidade_smooth");

  const handleMapLoad = React.useCallback(
    (event: MapEvent) => {
      if (imageNames) {
        const map = event.target;

        for (let imageName of imageNames) {
          const image = new Image();
          image.src = images[imageName];
          image.onload = function () {
            map.addImage(imageName, image, {
              pixelRatio: 2,
            });
          };
        }
      }

      if (onLoad) {
        onLoad(event);
      }
    },
    [imageNames, onLoad],
  );

  return (
    <Map
      {...props}
      onLoad={handleMapLoad}
      touchPitch={false}
      pitchWithRotate={false}
      dragRotate={false}
      minZoom={5}
      maxZoom={18}
      mapStyle={`https://tiles.stadiamaps.com/styles/${mapStyle}.json`}
      RTLTextPlugin={""}
      attributionControl={false}
      // onError={(e) => captureException(e.error)}
    >
      <NavigationControl showCompass={false} />
      <GeolocateControl />
      <StyleSwitcherControl style={mapStyle} onChange={(e) => setMapStyle(e.target.value)} />
      <AttributionControl compact={false} />
      {props.children}
    </Map>
  );
}
