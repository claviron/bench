<?php

declare(strict_types=1);

use Claviron\Bench\Workload;

require_once dirname(__DIR__).'/src/Workload.php';

$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$method = $_SERVER['REQUEST_METHOD'];
$allowed = match ($path) {
    '/bench/plain', '/bench/json' => ['GET', 'HEAD'],
    '/bench/echo' => ['POST'],
    default => [],
};

if (!$allowed) {
    http_response_code(404);
    header('Content-Type: text/plain');
    echo "not found\n";
    return;
}
if (!in_array($method, $allowed, true)) {
    http_response_code(405);
    header('Allow: '.implode(', ', $allowed));
    return;
}

[$content, $contentType] = match ($path) {
    '/bench/plain' => [Workload::PLAIN, 'text/plain'],
    '/bench/json' => [json_encode(Workload::json(), JSON_THROW_ON_ERROR), 'application/json'],
    '/bench/echo' => [file_get_contents('php://input'), 'application/octet-stream'],
};
if ($content === false) {
    throw new RuntimeException('Could not read the request body');
}
header('Content-Type: '.$contentType);
header('Content-Length: '.strlen($content));
if ($method !== 'HEAD') {
    echo $content;
}
