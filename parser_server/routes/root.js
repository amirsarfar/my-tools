"use strict";
const espree = require("espree");

module.exports = async function (fastify, opts) {
  fastify.get("/", async function (request, reply) {
    return { root: true };
  });
  fastify.post("/parse", async function (request, reply) {
    console.log(request.body);
    const ast = espree.parse(request.body, {
      loc: true,
      sourceType: "module",
      ecmaVersion: 2024,
      ecmaFeatures: {
        jsx: true,
      },
    });
    return { ast };
  });
};
