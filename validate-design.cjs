const fs = require("node:fs");
const path = require("node:path");
const Ajv2020 = require("../audit-repos/cloud-cost-guard/frontend/node_modules/ajv/dist/2020");

const root = __dirname;
const read = (relative) => JSON.parse(fs.readFileSync(path.join(root, relative), "utf8"));
const ajv = new Ajv2020({allErrors: true, strict: true, allowUnionTypes: true, validateFormats: false});

for (const name of [
  "common.schema.json",
  "tool-result.schema.json",
  "pipeline-manifest.schema.json",
  "trusted-report.schema.json",
  "verified-outcome.schema.json",
]) {
  ajv.addSchema(read(`schemas/${name}`));
}

const validFixtures = [
  ["fixtures/valid/minimal-finops-lite-result.json", "https://cloudandcapital.com/schemas/ccac/1.0.0/tool-result.schema.json"],
  ["fixtures/valid/minimal-trusted-report.json", "https://cloudandcapital.com/schemas/ccac/1.0.0/trusted-report.schema.json"],
];

for (const [fixture, schemaId] of validFixtures) {
  const validate = ajv.getSchema(schemaId);
  const ok = validate(read(fixture));
  if (!ok) {
    console.error(`${fixture} failed validation`);
    console.error(JSON.stringify(validate.errors, null, 2));
    process.exitCode = 1;
  } else {
    console.log(`valid: ${fixture}`);
  }
}

for (const name of fs.readdirSync(path.join(root, "fixtures/hostile"))) {
  read(`fixtures/hostile/${name}`);
  console.log(`hostile fixture parses: fixtures/hostile/${name}`);
}
