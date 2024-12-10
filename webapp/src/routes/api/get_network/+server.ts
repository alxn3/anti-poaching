import type { RequestHandler } from './$types';



export const POST: RequestHandler = async ({request}) =>{
    const {bbox} = await request.json();
    const cellUrl = new URL("https://www.opencellid.org/ajax/getCells.php");
    cellUrl.searchParams.set("bbox", bbox);
    console.log(cellUrl.href);
    const res = await fetch(cellUrl.href);
    return json(await res.json());
}