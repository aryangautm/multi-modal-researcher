import { z } from "zod";
import { Job } from "@/types";

const generateUUID = () => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
};

const formSchema = z.object({
  researchTopic: z
    .string()
    .min(10, "Research topic must be at least 10 characters long."),
  youtubeUrl: z
    .string()
    .url("Please enter a valid YouTube URL.")
    .optional()
    .or(z.literal("")),
});

export async function createResearchJob(
  formData: FormData
) {
  const data = {
    researchTopic: formData.get("researchTopic"),
    youtubeUrl: formData.get("youtubeUrl"),
  };

  const parsed = formSchema.safeParse(data);

  if (!parsed.success) {
    return {
      errors: parsed.error.flatten().fieldErrors,
      message: "Invalid form data.",
    };
  }

  // In a real application, this would call the GenAI flow and create a job in a database.
  // For this example, we simulate this by creating a new job object.
  const newJob: Job = {
    id: generateUUID(),
    researchTopic: parsed.data.researchTopic,
    youtubeUrl: parsed.data.youtubeUrl,
    status: "PENDING",
    summary: null,
    reportUrl: null,
    podcastUrl: null,
  };

  return { newJob, message: "Job created successfully." };
}