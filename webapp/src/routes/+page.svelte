<script lang="ts">
	import {
		MapLibre,
		MapEvents,
		DefaultMarker,
		GeoJSON,
		FillLayer,
		LineLayer,
		Popup,
		hoverStateFilter,
		Marker
	} from 'svelte-maplibre';
	import type { LngLat, LngLatBounds } from 'maplibre-gl';
	import IconChevonDown from 'virtual:icons/mdi/chevron-down';
	import IconChevonUp from 'virtual:icons/mdi/chevron-up';

	let layer_0: Map<number, any> = $state(new Map());
	let layer_1: Map<number, any> = $state(new Map());
	let layer_2: Map<number, any> = $state(new Map());

	let bounds: LngLatBounds | null = $state(null);
	let cellTowers: any[] = $state([]);
	let live: LngLat = $state([-80.424032921143, 37.22494287613821]);
	let hidden: boolean = $state(false);

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
			lng: -80.424032921143,
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

	const queryZones = async (layer_id: number, page: number) => {
		if (page > 5) return;
		const url = new URL(
			`https://services.arcgis.com/YnOQrIGdN9JGtBh4/arcgis/rest/services/Channel_${layer_id + 1}_Existing_Licenses/FeatureServer/0/query`
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
		url.searchParams.append('resultOffset', (page * 75).toString());
		url.searchParams.append('units', 'esriSRUnit_StatuteMile');

		const data = await (await fetch(url.href)).json();
		console.log(data);
		switch (layer_id) {
			case 0:
				layer_0 = new Map([...layer_0,...data['features'].map((v: any) => [v['id'], v])]);
				break;
			case 1:
				layer_1 = new Map([...layer_1,...data['features'].map((v: any) => [v['id'], v])]);
				break;
			case 2:
				layer_2 = new Map([...layer_2,...data['features'].map((v: any) => [v['id'], v])]);
				break;
		}
		if (data['properties'] && data['properties']['exceededTransferLimit']) {
			await queryZones(layer_id, page + 1);
		}
	};

	$effect(() => {
		if (!bounds) return;
		console.log(bounds);
		Promise.all([queryZones(0, 0), queryZones(1, 0), queryZones(2, 0)]);

		// (async () => {
		// 	const cellUrl = new URL('http://localhost:5173/cellmapper/getTowers');
		// 	cellUrl.searchParams.append('MCC', '310');
		// 	cellUrl.searchParams.append('MNC', '410');
		// 	cellUrl.searchParams.append('RAT', 'NR');
		// 	cellUrl.searchParams.append('boundsNELatitude', bounds._ne.lat.toString());
		// 	cellUrl.searchParams.append('boundsNELongitude', bounds._ne.lng.toString());
		// 	cellUrl.searchParams.append('boundsSWLatitude', bounds._sw.lat.toString());
		// 	cellUrl.searchParams.append('boundsSWLongitude', bounds._sw.lng.toString());
		// 	cellUrl.searchParams.append('filterFrequency', 'false');
		// 	cellUrl.searchParams.append('showOnlyMine', 'false');
		// 	cellUrl.searchParams.append('showUnverifiedOnly', 'false');
		// 	cellUrl.searchParams.append('showENDCOnly', 'false');
		// 	const data = await fetch(cellUrl.href, {
		// 		method: 'GET',
		// 		headers: {
		// 			'Content-Type': 'application/json'
		// 		}
		// 	});
		// 	console.log(data);
		// 	const json = await data.json();
		// 	const responseData = json['responseData'];
		// 	console.log(json);
		// 	if (responseData.length > 0) cellTowers = responseData;
		// 	console.log(cellTowers);
		// 	for (const tower of cellTowers) {
		// 		console.log(tower);
		// 	}
		// })();
	});

	let info: any = $state(null);

	// move live randomly
	$effect(() => {
		setInterval(() => {
			live = [live[0] + Math.random() * 0.001, live[1] + Math.random() * 0.001];
		}, 10);
	});

	$inspect({ layer_0, layer_1, layer_2, bounds, cellTowers, markers, info });
</script>

<MapLibre
	style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
	class="absolute left-0 top-0 aspect-video h-screen w-full sm:max-h-full"
	standardControls
	zoom={14}
	center={[-80.424032921143, 37.22494287613821]}
	onmoveend={(e) => {
		bounds = e.target.getBounds();
	}}
	onload={(e) => {
		bounds = e.getBounds();
	}}
>
	{#each [layer_0, layer_1, layer_2] as layer, i}
		<GeoJSON
			id={`id-${i}`}
			data={{ type: 'FeatureCollection', features: [...layer.values()] } as any}
			generateId
		>
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
				onclick={(e) => {
					info = e.features[0];
				}}
			>
				<Popup openOn="click" popupClass="rounded-lg" closeButton>
					{#if info && info.properties}
						<table class=" w-64 table-fixed">
							<tbody>
								<tr>
									<td><strong>Channel Designation</strong></td>
									<td>{info.properties['Channel_De']}</td>
								</tr>
								<tr>
									<td><strong>Associated MHz</strong> </td><td>{info.properties['Assoc_MHz_']}</td>
								</tr>
								<tr>
									<td><strong>Associated Channel</strong> </td><td
										>{info.properties['Assoc_Chan']}</td
									>
								</tr>
								<tr>
									<td><strong>Licensee</strong> </td><td>{info.properties['Licensee']}</td>
								</tr>
								<tr>
									<td><strong>Call Sign</strong></td>
									<td>{info.properties['CallSign']}</td>
								</tr>
								<tr>
									<td>ULS Link</td>
									<td>
										<a class="text-blue-500" href={info.properties['ULS_Link_1']} target="_blank"
											>{info.properties['ULS_Link_1']}</a
										>
									</td>
								</tr>
							</tbody>
						</table>
					{/if}
				</Popup>
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
	<Marker lngLat={live}>
		<div class="rounded-md bg-blue-500 p-1 text-white">🚗</div>
	</Marker>
	<!-- {#each cellTowers as tower}
		<DefaultMarker lngLat={[tower['longitude'], tower['latitude']]} />
	{/each} -->
</MapLibre>

<div class="absolute bottom-0 left-0 mb-10 ml-2 w-64 rounded-md bg-white p-2 text-xs">
	<div class="flex justify-between text-lg">
		<h1>Header</h1>
		<div class="inline-block h-8 w-5">
			{#if hidden}
				<button
					onclick={() => {
						hidden = false;
					}}
				>
					<IconChevonUp />
				</button>
			{:else}
				<button
					onclick={() => {
						hidden = true;
					}}
				>
					<IconChevonDown />
				</button>
			{/if}
		</div>
	</div>
	<div class={`${!hidden || 'hidden'}`}>Hello</div>
</div>

<!-- FID: 1416
GEOID_1:
NAME_1:
NAMELSAD_1:
Eligible_L:
Channel_De: Group 3 KG1-NG3 6 Channels
RS: ED
CallSign_B: WNC205
Assoc_MHz_: 2684.50000000-2690.00000000
Assoc_Chan: NG3
Licensee: The Salem City School Board
Amount: 17.5
CallSign: WNC205
ULS_Link_1: https://wireless2.fcc.gov/UlsApp/UlsSearch/license.jsp?licKey=2586579
Amt_2: 17.5
Amt_3: 17.5
Shape__Area: 15809677111.582031
Shape__Length: 445739.11146429426 -->

<style>
	tr {
		word-wrap: break-word;
		vertical-align: top;
	}

	tr td:first-child {
		font-weight: bold;
		width: 40%;
		word-wrap: break-word;
	}
</style>
