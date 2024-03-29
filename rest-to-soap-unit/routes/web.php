<?php

use Illuminate\Http\Request;
use Illuminate\Http\Response;

/** @var \Laravel\Lumen\Routing\Router $router */

/*
|--------------------------------------------------------------------------
| Application Routes
|--------------------------------------------------------------------------
|
| Here is where you can register all of the routes for an application.
| It is a breeze. Simply tell Lumen the URIs it should respond to
| and give it the Closure to call when that URI is requested.
|
*/

$router->post(
    '/api/{service}/{port}/{method}',
    function (Request $request, $service, $port, $method) {
        $client = getSoapClient($request);
        if (!$client) {
            return response()->json('wsdl not set', 500);
        }
        $json = $request->getContent();
        $data = json_decode($json, true);
        try {
        $response = $client->__soapCall($method, array($data));
        } catch(SoapFault $soapFault) {
            return response()->json($soapFault->faultstring, 500);
        }
        return response()->json($response);
    }
);

$router->get(
    '/health',
    function () {
        return response()->json(['status' => 'ok']);
    }
);

function getSoapClientOptions($authorizationHeader = null, $options = []) {
    $verify_peer = getenv("VERIFY_PEER");
    if (!$verify_peer || strlen($verify_peer) <= 0) {
        $verify_peer = false;
    } else {
        $verify_peer = true;
    }
    $verify_peer_name = getenv("VERIFY_PEER_NAME");
    if (!$verify_peer_name || strlen($verify_peer_name) <= 0) {
        $verify_peer_name = false;
    } else {
        $verify_peer_name = true;
    }
    $allow_self_signed = getenv("ALLOW_SELF_SIGNED");
    if (!$allow_self_signed || strlen($allow_self_signed) <= 0) {
        $allow_self_signed = true;
    } else {
        $allow_self_signed = false;
    }
    
    $context = stream_context_create([
        'ssl' => [
            // set some SSL/TLS specific options
            'verify_peer' => $verify_peer,
            'verify_peer_name' => $verify_peer_name,
            'allow_self_signed' => $allow_self_signed
        ],
        'http' => [
            'header' => "Authorization: $authorizationHeader"
        ],
    ]);
    $options = array_merge([
        'cache_wsdl' => WSDL_CACHE_NONE,
        'exceptions' => true,
        'soap_version' => SOAP_1_1,
        'trace' => true,
        'stream_context' => $context,
    ], $options);
    return $options;
}

function getSoapClient($request, $options = [])
{
    $wsdl = getenv("SOAP_URL");
    if (!$wsdl || strlen($wsdl) <= 0) {
        return null;
    }
    $authorizationHeader = $request->header("Authorization");
    if (!$authorizationHeader) {
        $authorizationHeader = "None";
    }
    $options = getSoapClientOptions($authorizationHeader, $options);
    $client = new SoapClient($wsdl, $options);
    return $client;
}
