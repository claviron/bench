# PHP, Laravel and Symfony workloads

One optional Composer development package supplies the workload code. It does
not install a runner or register routes automatically. The PHP constraint is
the package minimum, not a claim that Symfony 8 runs on PHP 8.2; use the PHP
version required by the application's own manifest.

Install the published package from Packagist:

```sh
composer require --dev claviron/bench
```

No install/update is performed by this repository. Development packages remain
available in the isolated benchmark installation, even when measuring `APP_ENV=prod` with
debug/profilers disabled. Do not expose these routes in a production deployment.

## Plain PHP

Point the runner's existing script entry at `vendor/claviron/bench/public/index.php`.
The file has no Composer or framework dependency and can run on any ordinary
PHP request runtime. Socket/process ownership stays with that runtime.

## Laravel

Explicitly load the package's `routes/laravel.php` through the application's
existing route registration, for example in an isolated benchmark route file:

```php
require base_path('vendor/claviron/bench/routes/laravel.php');
```

Choose the route middleware deliberately. `web` CSRF protection may reject echo
POSTs without a CSRF token; do not silently remove security middleware from an
existing application just to obtain a measurement. JSON is serialized through
Laravel's response helper for each request.

## Symfony

Register `Claviron\Bench\Symfony\BenchController` as an autowired,
autoconfigured service using the application's existing service configurator.
For example, a `config/services.php` entry can use:

```php
use Claviron\Bench\Symfony\BenchController;
use Symfony\Component\DependencyInjection\Loader\Configurator\ContainerConfigurator;

return static function (ContainerConfigurator $container): void {
    $container->services()->set(BenchController::class)->autowire()->autoconfigure();
};
```

Merge this registration into the existing configurator if one is present;
do not replace the application's other service definitions.
Import its attributes through a PHP route configurator:

```php
use Symfony\Component\Routing\Loader\Configurator\RoutingConfigurator;

return static function (RoutingConfigurator $routes): void {
    $routes->import(
        '../../vendor/claviron/bench/src/Symfony/BenchController.php',
        'attribute',
    );
};
```

This example belongs under `config/routes/`. The controller uses framework
HTTP request/response and routing APIs, no Doctrine, Twig or persistence.
Framework and PHP versions must be recorded with a measurement.

## Package identity

Composer package: `claviron/bench`. PHP namespace: `Claviron\Bench`.
Sources live in `claviron/bench`; releases are exported to `claviron/php-bench`
and indexed by Packagist from their Git tags. No Claviron, Gufi or Lumenize
runtime is required. Licensed under MIT or Apache-2.0; see `LICENSE`.
