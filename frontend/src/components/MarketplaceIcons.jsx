import React from "react";

export const AmazonIcon = ({ className = "w-6 h-6" }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path
      d="M13.418 12.247c-1.637-.22-3.41.135-4.662 1.258-1.503 1.34-1.282 3.398.243 4.298 1.48.87 3.518.57 4.773-.553.308.452.883.824 1.405.824.787 0 1.268-.535 1.268-1.31v-4.517H13.42v.002zm.172 3.864c-.66.69-1.874.966-2.617.51-.715-.443-.728-1.531.066-2.146.685-.533 1.777-.665 2.551-.497v2.133z"
      fill="#FF9900"
    />
    <path
      d="M19.167 17.652c-2.484 1.837-6.096 2.802-9.215 2.802-4.364 0-8.293-1.848-11.232-4.941-.23-.243-.025-.572.274-.384 3.167 1.996 7.07 3.197 11.082 3.197 2.766 0 5.76-.665 8.441-2.046.415-.213.784.288.65.572z"
      fill="#FF9900"
    />
    <path
      d="M19.82 16.51c.32-.41.98-.38 1.31.05.77 1.01 1.63 2.14 1.75 2.3.15.2.03.49-.22.49-.63.02-2.8-.23-3.69-1.3-.18-.21-.02-.48.22-.48.16 0 .39.06.63.12l-.004-.002z"
      fill="#FF9900"
    />
  </svg>
);

export const FlipkartIcon = ({ className = "w-6 h-6" }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect width="24" height="24" rx="4" fill="#2874F0" />
    <path
      d="M6 6H18V18H6V6Z"
      fill="#FFE500"
    />
    <path
      d="M14.5 8.5H10.5V11H13.5V13.5H10.5V16H8V6H14.5V8.5Z"
      fill="#2874F0"
    />
  </svg>
);

export const MeeshoIcon = ({ className = "w-6 h-6" }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect width="24" height="24" rx="6" fill="#F43397" />
    <path
      d="M6.5 17V7L10 13.5L13.5 7V17H11.5V10.5L9.5 14.2L7.5 10.5V17H6.5ZM14.5 17V7H17.5C18.6 7 19.5 7.9 19.5 9V11C19.5 12.1 18.6 13 17.5 13H16V17H14.5ZM16 11.5H17.5C17.8 11.5 18 11.3 18 11V9C18 8.7 17.8 8.5 17.5 8.5H16V11.5Z"
      fill="#FFFFFF"
    />
  </svg>
);

export const MarketplaceIcon = ({ marketplace, className = "w-6 h-6" }) => {
  const mp = (marketplace || "").toLowerCase();
  if (mp === "amazon") return <AmazonIcon className={className} />;
  if (mp === "flipkart") return <FlipkartIcon className={className} />;
  if (mp === "meesho") return <MeeshoIcon className={className} />;
  return null;
};
