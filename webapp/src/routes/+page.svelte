<script lang="ts">
	import {
		MapLibre,
		MapEvents,
		DefaultMarker,
		GeoJSON,
		FillLayer,
		LineLayer,
		Popup,
		hoverStateFilter
	} from 'svelte-maplibre';
	import type { LngLatBounds } from 'maplibre-gl';

	let layers: GeoJSON[3] | null = $state(null);
	let bounds: LngLatBounds | null = $state(null);

	let markers: {
		mcc: number;
		mnc: number;
		lac: number;
		cid: number;
		lng: number;
		lat: number;
		speed: number;
		timestamp: number;
	}[] = $state([
		{
			mcc: 310,
			mnc: 260,
			lac: 100,
			cid: 100,
			lng:-80.424032921143,
			lat: 37.22494287613821,
			speed: 0,
			timestamp: Date.now()
		}
	]);

	$effect(() => {
		const ws_url = new URL('/websocket', window.location.href).href;
		const ws = new WebSocket(ws_url);
		ws.onmessage = (event) => {
			try {
				const raw = JSON.parse(event.data);
				console.log(raw);
				const data = raw.data;
				console.log(data);
				if (raw.type === 'pins') {
					markers = markers.concat(data);
					console.log(markers);
				}
			} catch (e) {
				console.log(event.data);
			}
		};
	});

	$effect(() => {
		if (!bounds) return;
		Promise.all(
			[1, 2, 3].map(async (i) => {
				const url = new URL(
					`https://services.arcgis.com/YnOQrIGdN9JGtBh4/arcgis/rest/services/Channel_${i}_Existing_Licenses/FeatureServer/0/query`
				);
				url.searchParams.append('f', 'geojson');
				url.searchParams.append('where', '1=1');
				url.searchParams.append('geometryType', 'esriGeometryEnvelope');
				url.searchParams.append('spatialRel', 'esriSpatialRelIntersects');
				url.searchParams.append('outFields', '*');
				url.searchParams.append(
					'geometry',
					JSON.stringify({
						xmin: bounds?.getWest(),
						ymin: bounds?.getSouth(),
						xmax: bounds?.getEast(),
						ymax: bounds?.getNorth()
					})
				);
				url.searchParams.append('resultRecordCount', '75');
				url.searchParams.append('units', 'esriSRUnit_StatuteMile');

				const data = await fetch(url.href);
				return await data.json();
			})
		)
			.then((data) => {
				layers = data;
			})
			.catch((error) => {
				console.error(error);
			});
	});

	let info: any = $state(null);
</script>

<MapLibre
	style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
	class="absolute left-0 top-0 aspect-video h-screen w-full sm:max-h-full"
	standardControls
	zoom={7}
	center={[-80.424032921143, 37.22494287613821]}
	onmoveend={(e) => {
		bounds = e.target.getBounds();
	}}
	onload={(e) => {
		bounds = e.getBounds();
	}}
>
	{#each layers as layer, i}
		<GeoJSON id={`id-${i}`} data={layer as any} generateId>
			<LineLayer
				id={`line-${i}`}
				layout={{
					'line-cap': 'round',
					'line-join': 'round'
				}}
				paint={{
					'line-color': i % 3 === 0 ? '#e94444' : i % 3 === 1 ? '#44e944' : '#4444e9',
					'line-width': 2,
					'line-opacity': hoverStateFilter(0.025, 0.3)
				}}
			/>
			<FillLayer
				id={`fill-${i}`}
				paint={{
					'fill-color': i % 3 === 0 ? '#e94444' : i % 3 === 1 ? '#44e944' : '#4444e9',
					'fill-opacity': 0.01
				}}
				interactive
				manageHoverState
				on:click={(e) => {
					info = e.detail.features[0];
				}}
			>
				<!-- <Popup let:data>
					{#if data && data.properties}
						{#each Object.entries(data.properties) as [key, value]}
							<p>{key}: {value}</p>
						{/each}
					{/if}
				</Popup> -->
			</FillLayer>
		</GeoJSON>
	{/each}
	<!-- <MapEvents on:click={(e) => {
		// if right click
			markers = [...markers, { lngLat: e.detail.lngLat.toArray() }];
	}}/> -->
	{#each markers as marker}
		<DefaultMarker lngLat={[marker.lng, marker.lat]} />
	{/each}
</MapLibre>

<div class="absolute right-0 top-0 m-1 rounded-md bg-white p-2 text-xs">
	{#if info}
		{#each Object.entries(info.properties) as [key, value]}
			<p>{key}: {value}</p>
		{/each}
	{/if}
</div>
