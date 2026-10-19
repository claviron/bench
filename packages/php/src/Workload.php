<?php

declare(strict_types=1);

namespace Claviron\Bench;

final class Workload
{
    public const PLAIN = "ok\n";

    /** @return array{message: string} */
    public static function json(): array
    {
        return ['message' => 'ok'];
    }
}
