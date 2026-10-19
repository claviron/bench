<?php

declare(strict_types=1);

namespace Claviron\Bench\Symfony;

use Claviron\Bench\Workload;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Attribute\Route;

final class BenchController extends AbstractController
{
    #[Route('/bench/plain', name: 'claviron_bench_plain', methods: ['GET', 'HEAD'], stateless: true)]
    public function plain(): Response
    {
        return new Response(Workload::PLAIN, headers: ['Content-Type' => 'text/plain']);
    }

    #[Route('/bench/json', name: 'claviron_bench_json', methods: ['GET', 'HEAD'], stateless: true)]
    public function jsonResponse(): JsonResponse
    {
        return new JsonResponse(Workload::json());
    }

    #[Route('/bench/echo', name: 'claviron_bench_echo', methods: ['POST'], stateless: true)]
    public function echoBody(Request $request): Response
    {
        return new Response($request->getContent(), headers: ['Content-Type' => 'application/octet-stream']);
    }
}
