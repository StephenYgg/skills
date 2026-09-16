# Template Admin API

Read this reference when API routing, current-version resolution, or RuleFile retrieval is part of the task.

## Production Gateway

Use this external base URL:

```text
https://webapi.octoparse.com/v1/templateService
```

The Template service controller route is:

```text
api/templateservice/admin/templates
```

The production gateway maps the public `/v1/templateService/*` prefix to the Template service route. Do not substitute the legacy `/api/templates/*` route.

## Read Sequence

```text
GET /admin/templates/{templateId}
GET /admin/templates/{templateId}/versions/{currentVersionId}
GET /admin/templates/{templateId}/versions/{currentVersionId}/parameters  # optional normalized parameters
```

The first response supplies `data.currentVersion.templateVersionId`. Use that exact ID for version retrieval; do not assume the numerically largest version is current.

The version response is a `TemplateVersionDto` and includes `body` (Base64), `parameters`, `type`, `settings`, and `ruleFile`. Download the URL in `ruleFile`; do not treat the URL string itself as the execution file.

Gateway responses normally have this envelope:

```json
{
  "data": {},
  "requestId": null,
  "error": null
}
```

Treat a non-null `error`, missing `data`, missing current version, blank `ruleFile`, an HTTP error, or an empty download as a failure. Admin writes require separate user authorization.

## Code Sources

- `Template/src/Octopus.Template.HttpApi/Controllers/Admin/TemplateController.cs`
- `Template/src/Octopus.Template.Application.Contracts/TemplateVersions/Dtos/TemplateVersionDto.cs`
- `bc-apigateway` YARP configuration; production routing is Nacos-backed, while local Debug config documents the service route and a separate legacy route.
