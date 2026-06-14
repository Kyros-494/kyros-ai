/**
 * Kyros Website - Sitemap Generation
 *
 * Automatically generates sitemap.xml for SEO.
 * See: https://nextjs.org/docs/app/api-reference/file-conventions/metadata/sitemap
 */

import { MetadataRoute } from "next";

export const dynamic = "force-static";

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://kyros-494.github.io/kyros-ai";

  const paths = [
    { url: baseUrl, priority: 1.0, changeFrequency: "weekly" as const },
    { url: `${baseUrl}/docs`, priority: 0.9, changeFrequency: "weekly" as const },
    { url: `${baseUrl}/developers`, priority: 0.8, changeFrequency: "weekly" as const },
    { url: `${baseUrl}/usecases`, priority: 0.8, changeFrequency: "weekly" as const },
    { url: `${baseUrl}/simulation`, priority: 0.8, changeFrequency: "weekly" as const },
    { url: `${baseUrl}/architecture`, priority: 0.7, changeFrequency: "monthly" as const },
  ];

  return paths.map((p) => ({
    url: p.url,
    lastModified: new Date(),
    changeFrequency: p.changeFrequency,
    priority: p.priority,
  }));
}
