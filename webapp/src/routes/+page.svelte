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
		Marker,
		MarkerLayer,
		SymbolLayer,
		CircleLayer
	} from 'svelte-maplibre';
	import type { Feature, Geometry } from 'geojson';
	import type { LngLat, LngLatBounds } from 'maplibre-gl';
	import IconChevonDown from 'virtual:icons/mdi/chevron-down';
	import IconChevonUp from 'virtual:icons/mdi/chevron-up';
	import IconTransmissionTower from 'virtual:icons/mdi/transmission-tower';
	import MCC_MNC_LOOKUP from '$lib/mcc_mnc_lookup';

	let layer_0: Map<number, any> = $state(new Map());
	let layer_1: Map<number, any> = $state(new Map());
	let layer_2: Map<number, any> = $state(new Map());

	let cellTowerData: Map<number, any> = new Map();
	let cellTowers: Set<number> = new Set();
	let cellTowerJson: any = $state({
		type: 'FeatureCollection',
		features: []
	});
	const cellStepX = 0.025;
	const cellStepY = 0.025;
	const rowLength = 180 / cellStepX;

	let bounds: LngLatBounds | null = $state(null);
	let live: LngLat = $state([-80.424032921143, 37.22494287613821]);
	let hidden: boolean = $state(false);
	let zoom: number = $state(14);
	const maxSqMeters = 12000000;

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
		// console.log(data);
		switch (layer_id) {
			case 0:
				layer_0 = new Map([...layer_0, ...data['features'].map((v: any) => [v['id'], v])]);
				break;
			case 1:
				layer_1 = new Map([...layer_1, ...data['features'].map((v: any) => [v['id'], v])]);
				break;
			case 2:
				layer_2 = new Map([...layer_2, ...data['features'].map((v: any) => [v['id'], v])]);
				break;
		}
		if (data['properties'] && data['properties']['exceededTransferLimit']) {
			await queryZones(layer_id, page + 1);
		}
	};

	const queryCellTowers = async (x: number, y: number) => {
		const lat = y / 40 - 90;
		const lon = x / 40 - 180;
		const data = await (
			await fetch('/api/cell-towers', {
				method: 'POST',
				body: JSON.stringify({
					bbox: `${lon - cellStepX / 2}\,${lat - cellStepY / 2}\,${lon + cellStepX / 2}\,${lat + cellStepY / 2}`
				}),
				headers: {
					'Content-Type': 'application/json'
				}
			})
		).json();
		console.log(data);
		cellTowerData.set(
			y * rowLength + x,
			data['features'].filter(
				(v: any) => v['properties']['radio'] === 'LTE' || v['properties']['radio'] === 'NR'
			)
		);
	};

	const getCellTowers = async () => {
		if (!bounds) return;
		for (let lon = bounds._ne.lng; lon > bounds._sw.lng; lon -= cellStepX) {
			for (let lat = bounds._ne.lat; lat > bounds._sw.lat; lat -= cellStepY) {
				const x = Math.floor((lon + 180) / cellStepX);
				const y = Math.floor((lat + 90) / cellStepY);
				const id = y * rowLength + x;
				if (!cellTowerData.has(id)) await queryCellTowers(x, y);
				cellTowers = new Set([...cellTowers, id]);
			}
		}
	};

	$effect(() => {
		if (!bounds) return;
		// console.log(bounds);
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

	$effect(() => {
		if (zoom >= 14) {
			getCellTowers().then(() => {
				console.log(cellTowerData);
				cellTowerJson = {
					type: 'FeatureCollection',
					features: [...cellTowers]
						.map((curr) => {
							const x = curr % rowLength;
							const y = Math.floor(curr / rowLength);
							return cellTowerData.get(curr);
						})
						.reduce((acc, val) => acc.concat(val), [])
				};
				console.log(cellTowerJson);
			});
		}
	});

	// move live randomly
	$effect(() => {
		setInterval(() => {
			live = [live[0] + Math.random() * 0.001, live[1] + Math.random() * 0.001];
		}, 10);
	});

	// $inspect({ layer_0, layer_1, layer_2, bounds, cellTowers, markers, info });
</script>

<MapLibre
	style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
	class="absolute left-0 top-0 aspect-video h-screen w-full sm:max-h-full"
	standardControls
	{zoom}
	center={[-80.424032921143, 37.22494287613821]}
	onmoveend={(e) => {
		zoom = e.target.getZoom();
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
			></FillLayer>
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
	<GeoJSON
		id="towers"
		data={cellTowerJson as any}
		cluster={{
			radius: 500,
			maxZoom: 15
		}}
	>
		<!-- Markers -->

		<CircleLayer
			id="cluster_circles"
			applyToClusters
			hoverCursor="pointer"
			paint={{
				// Use step expressions (https://maplibre.org/maplibre-gl-js-docs/style-spec/#expressions-step)
				// with three steps to implement three types of circles:
				//   * Blue, 20px circles when point count is less than 100
				//   * Yellow, 30px circles when point count is between 100 and 750
				//   * Pink, 40px circles when point count is greater than or equal to 750
				'circle-color': ['step', ['get', 'point_count'], '#51bbd6', 5, '#f1f075', 20, '#f28cb1'],
				'circle-radius': ['step', ['get', 'point_count'], 20, 5, 25, 20, 30],
				'circle-opacity': hoverStateFilter(0.5, 0.8),
				'circle-stroke-color': [
					'step',
					['get', 'point_count'],
					'#51bbd6',
					5,
					'#f1f075',
					20,
					'#f28cb1'
				],
				'circle-stroke-width': 2,
				'circle-stroke-opacity': hoverStateFilter(0.7, 1)
			}}
			manageHoverState
			onclick={(e) => {
				// move to cluster
				e.map.flyTo({
					center: e.features[0].geometry.coordinates as LngLat,
					zoom: e.map.getZoom() + 1
				});
			}}
		></CircleLayer>

		<SymbolLayer
			id="cluster_labels"
			interactive={false}
			applyToClusters
			layout={{
				'text-field': ['format', ['get', 'point_count_abbreviated'], { 'font-scale': 1 }],
				'text-size': 18,
				'text-offset': [0, 0]
			}}
		/>
		<MarkerLayer applyToClusters={false} asButton>
			{#snippet children({
				feature
			}: {
				feature: GeoJSON.Feature<
					GeoJSON.Point,
					{
						area: number;
						cell: number;
						created: Date;
						mcc: number;
						net: number;
						radio: string;
						range: number;
						samples: number;
						updated: Date;
					}
				>;
			})}
				{@const props = feature.properties}
				{@const mccmncc = `${props.mcc}${props.net}`}
				<IconTransmissionTower
					class={`rounded-lg p-1 text-lg text-white ${(() => {
						switch (mccmncc) {
							case '310680':
							case '310560':
							case '310380':
							case '310410':
							case '310150':
							case '310170':
							case '310280':
							case '31030':
							case '310980':
							case '310990':
								return 'bg-blue-500';
							case '310800':
							case '31031':
							case '31026':
							case '310200':
							case '310210':
							case '310220':
							case '310230':
							case '310240':
							case '310250':
							case '310260':
							case '310270':
							case '310330':
							case '310310':
							case '310160':
							case '310290':
							case '310660':
							case '310580':
							case '310490':
								return 'bg-green-500';
							case '3104':
							case '3105':
							case '31012':
							case '311480':
							case '311481':
							case '311482':
							case '311483':
							case '311484':
							case '311485':
							case '311486':
							case '311487':
							case '311488':
							case '311489':
							case '311390':
							case '311270':
							case '311271':
							case '311272':
							case '311273':
							case '311274':
							case '311275':
							case '311276':
							case '311277':
							case '311278':
							case '311279':
							case '311280':
							case '311281':
							case '311282':
							case '311283':
							case '311284':
							case '311285':
							case '311286':
							case '311287':
							case '311288':
							case '311289':
							case '31112':
								return 'bg-red-500';
							default:
								return 'bg-gray-500';
						}
					})()}`}
				/>
				<Popup openOn="hover" closeOnClickInside>
					<h1 class="font-bold text-lg">{MCC_MNC_LOOKUP[`${props.mcc}${props.net}`]?.Network}</h1>
					<table class="w-40">
						<tbody>
							<tr>
								<td>Area</td>
								<td>{props.area}</td>
							</tr>
							<tr>
								<td>Cell</td>
								<td>{props.cell}</td>
							</tr>
							<tr>
								<td>MCC</td>
								<td>{props.mcc}</td>
							</tr>
							<tr>
								<td>Net</td>
								<td>{props.net}</td>
							</tr>
							<tr>
								<td>Radio</td>
								<td>{props.radio}</td>
							</tr>
							<tr>
								<td>Range</td>
								<td>{props.range}</td>
							</tr>
							<tr>
								<td>Samples</td>
								<td>{props.samples}</td>
							</tr>
							<tr>
								<td>Created</td>
								<td>{new Date(props.created * 1000).toString()}</td>
							</tr>
							<tr>
								<td>Updated</td>
								<td>{new Date(props.updated * 1000).toString()}</td>
							</tr>
						</tbody>
					</table>
				</Popup>
			{/snippet}
		</MarkerLayer>
	</GeoJSON>
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
	<div class={`${!hidden || 'hidden'}`}>
		{#if info && info.properties}
			<table class="w-full table-fixed">
				<tbody>
					<tr>
						<td>Channel Designation</td>
						<td>{info.properties['Channel_De']}</td>
					</tr>
					<tr>
						<td>Associated MHz </td><td>{info.properties['Assoc_MHz_']}</td>
					</tr>
					<tr>
						<td>Associated Channel </td><td>{info.properties['Assoc_Chan']}</td>
					</tr>
					<tr>
						<td>Licensee </td><td>{info.properties['Licensee']}</td>
					</tr>
					<tr>
						<td>Call Sign</td>
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
	</div>
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
