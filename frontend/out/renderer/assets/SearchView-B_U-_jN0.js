import { _ as _export_sfc, o as onBeforeUnmount, c as createElementBlock, a as createBaseVNode, w as withDirectives, v as vShow, n as normalizeClass, F as Fragment, t as toDisplayString, b as createTextVNode, d as createCommentVNode, r as renderList, e as createBlock, f as createVNode, g as withCtx, T as Transition, h as Teleport, i as withModifiers, j as normalizeStyle, k as ref, l as openBlock } from "./index-B3Su-Vh6.js";
const API_BASE = "http://127.0.0.1:8000";
async function loadLocalGallery(folderPath) {
  let response;
  try {
    response = await fetch(`${API_BASE}/retrieve/log/local/gallery`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ folderPath })
    });
  } catch {
    throw new Error("请求未到达后端或响应被浏览器拦截（后端可能 500），请查看 Network 面板");
  }
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") {
        detail = body.detail;
      }
    } catch {
    }
    throw new Error(`加载图库失败（${detail}）`);
  }
  const result = await response.json();
  const data = typeof result?.data === "string" ? JSON.parse(result.data) : result?.data;
  return Array.isArray(data) ? data : [];
}
function resolveImageUrl(imageUrl) {
  return `${API_BASE}${imageUrl}`;
}
const _hoisted_1 = { class: "search-page" };
const _hoisted_2 = ["title"];
const _hoisted_3 = { class: "toolbar__label" };
const _hoisted_4 = { class: "content" };
const _hoisted_5 = { class: "panel-col" };
const _hoisted_6 = { class: "card query-card" };
const _hoisted_7 = ["src", "alt"];
const _hoisted_8 = { class: "query-card__name" };
const _hoisted_9 = {
  key: 1,
  class: "card-empty"
};
const _hoisted_10 = { class: "query-actions" };
const _hoisted_11 = ["disabled"];
const _hoisted_12 = { class: "panel-col panel-col--results" };
const _hoisted_13 = { class: "card result-card" };
const _hoisted_14 = {
  key: 0,
  class: "result-card__count"
};
const _hoisted_15 = {
  key: 1,
  class: "card-empty"
};
const _hoisted_16 = {
  key: 2,
  class: "result-error"
};
const _hoisted_17 = {
  key: 3,
  class: "result-grid"
};
const _hoisted_18 = ["src", "alt", "title"];
const _hoisted_19 = {
  key: 4,
  class: "card-empty"
};
const _hoisted_20 = { class: "dir-group" };
const _hoisted_21 = ["title"];
const _hoisted_22 = { class: "dir-display__text" };
const _hoisted_23 = {
  key: 0,
  class: "toast",
  role: "status"
};
const _hoisted_24 = ["src", "alt"];
const _sfc_main = {
  __name: "SearchView",
  setup(__props) {
    const toolbarCollapsed = ref(false);
    function toggleToolbar() {
      toolbarCollapsed.value = !toolbarCollapsed.value;
    }
    const fileInput = ref(null);
    const queryImage = ref(null);
    let queryObjectUrl = null;
    function triggerPickImage() {
      fileInput.value?.click();
    }
    function onFileChange(event) {
      const file = event.target.files?.[0];
      if (!file) return;
      if (queryObjectUrl) URL.revokeObjectURL(queryObjectUrl);
      queryObjectUrl = URL.createObjectURL(file);
      queryImage.value = { url: queryObjectUrl, name: file.name };
      event.target.value = "";
    }
    function clearQueryImage() {
      if (queryObjectUrl) URL.revokeObjectURL(queryObjectUrl);
      queryObjectUrl = null;
      queryImage.value = null;
    }
    const ctxMenu = ref({ visible: false, x: 0, y: 0 });
    const lightboxVisible = ref(false);
    function openCtxMenu(event) {
      event.preventDefault();
      if (!queryImage.value) return;
      const x = Math.min(event.clientX, window.innerWidth - 170);
      const y = Math.min(event.clientY, window.innerHeight - 150);
      ctxMenu.value = { visible: true, x, y };
    }
    function closeCtxMenu() {
      ctxMenu.value.visible = false;
    }
    function ctxZoom() {
      closeCtxMenu();
      lightboxVisible.value = true;
    }
    async function ctxCopyPath() {
      closeCtxMenu();
      try {
        await navigator.clipboard.writeText(queryImage.value?.name ?? "");
        showToast("已复制文件名（浏览器无法获取完整本地路径）");
      } catch {
        showToast("复制失败");
      }
    }
    function ctxDownload() {
      closeCtxMenu();
      if (!queryImage.value) return;
      const link = document.createElement("a");
      link.href = queryImage.value.url;
      link.download = queryImage.value.name;
      link.click();
    }
    function startSearch() {
      if (!queryImage.value) return;
      showToast("后端检索接口尚未接入，敬请期待");
    }
    const toastMessage = ref("");
    const toastVisible = ref(false);
    let toastTimer = null;
    function showToast(message) {
      toastMessage.value = message;
      toastVisible.value = true;
      clearTimeout(toastTimer);
      toastTimer = setTimeout(() => {
        toastVisible.value = false;
      }, 2600);
    }
    onBeforeUnmount(() => {
      if (queryObjectUrl) URL.revokeObjectURL(queryObjectUrl);
      clearTimeout(toastTimer);
    });
    const galleryImages = ref([]);
    const galleryFolder = ref("");
    const galleryLoading = ref(false);
    const galleryError = ref("");
    async function selectDirectory() {
      if (!window.api?.selectDirectory) {
        showToast("目录选择需在 Electron 桌面端使用");
        return;
      }
      const folderPath = await window.api.selectDirectory();
      if (!folderPath) return;
      galleryLoading.value = true;
      galleryError.value = "";
      try {
        const images = await loadLocalGallery(folderPath);
        galleryFolder.value = folderPath;
        galleryImages.value = images.map((item) => ({
          name: item.name,
          url: resolveImageUrl(item.imageUrl)
        }));
      } catch (error) {
        galleryError.value = error instanceof Error ? error.message : String(error);
      } finally {
        galleryLoading.value = false;
      }
    }
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("aside", {
          class: normalizeClass(["toolbar", { "toolbar--collapsed": toolbarCollapsed.value }])
        }, [
          createBaseVNode("button", {
            class: "toolbar__back",
            type: "button",
            title: toolbarCollapsed.value ? "展开工具栏" : "收起工具栏",
            onClick: toggleToolbar
          }, [..._cache[1] || (_cache[1] = [
            createBaseVNode("svg", {
              viewBox: "0 0 24 24",
              width: "18",
              height: "18",
              fill: "none",
              "aria-hidden": "true"
            }, [
              createBaseVNode("path", {
                d: "M15 5l-7 7 7 7",
                stroke: "currentColor",
                "stroke-width": "2.2",
                "stroke-linecap": "round",
                "stroke-linejoin": "round"
              })
            ], -1)
          ])], 8, _hoisted_2),
          withDirectives(createBaseVNode("span", _hoisted_3, "工具栏", 512), [
            [vShow, !toolbarCollapsed.value]
          ])
        ], 2),
        createBaseVNode("div", _hoisted_4, [
          createBaseVNode("section", _hoisted_5, [
            createBaseVNode("div", _hoisted_6, [
              queryImage.value ? (openBlock(), createElementBlock(Fragment, { key: 0 }, [
                createBaseVNode("img", {
                  class: "query-card__img",
                  src: queryImage.value.url,
                  alt: queryImage.value.name,
                  onContextmenu: openCtxMenu
                }, null, 40, _hoisted_7),
                createBaseVNode("button", {
                  class: "query-card__remove",
                  type: "button",
                  title: "移除图片",
                  onClick: clearQueryImage
                }, [..._cache[2] || (_cache[2] = [
                  createBaseVNode("svg", {
                    viewBox: "0 0 24 24",
                    width: "14",
                    height: "14",
                    fill: "none",
                    "aria-hidden": "true"
                  }, [
                    createBaseVNode("path", {
                      d: "M6 6l12 12M18 6L6 18",
                      stroke: "currentColor",
                      "stroke-width": "2.4",
                      "stroke-linecap": "round"
                    })
                  ], -1)
                ])]),
                createBaseVNode("span", _hoisted_8, toDisplayString(queryImage.value.name), 1)
              ], 64)) : (openBlock(), createElementBlock("div", _hoisted_9, [..._cache[3] || (_cache[3] = [
                createBaseVNode("svg", {
                  class: "card-empty__icon",
                  viewBox: "0 0 48 48",
                  fill: "none",
                  "aria-hidden": "true"
                }, [
                  createBaseVNode("rect", {
                    x: "5",
                    y: "9",
                    width: "38",
                    height: "30",
                    rx: "4",
                    stroke: "currentColor",
                    "stroke-width": "2.6"
                  }),
                  createBaseVNode("circle", {
                    cx: "17",
                    cy: "19",
                    r: "3.4",
                    fill: "currentColor"
                  }),
                  createBaseVNode("path", {
                    d: "M9 34l10-10 7 7 5-5 8 8",
                    stroke: "currentColor",
                    "stroke-width": "2.6",
                    "stroke-linecap": "round",
                    "stroke-linejoin": "round"
                  })
                ], -1),
                createBaseVNode("p", null, [
                  createTextVNode("点击下方「选择图片」"),
                  createBaseVNode("br"),
                  createTextVNode("上传要检索的图片")
                ], -1)
              ])]))
            ]),
            createBaseVNode("input", {
              ref_key: "fileInput",
              ref: fileInput,
              class: "visually-hidden",
              type: "file",
              accept: "image/*",
              onChange: onFileChange
            }, null, 544),
            createBaseVNode("div", _hoisted_10, [
              createBaseVNode("button", {
                class: "pill-btn",
                type: "button",
                onClick: triggerPickImage
              }, " 选 择 图 片 "),
              createBaseVNode("button", {
                class: "pill-btn pill-btn--primary",
                type: "button",
                title: "上传查询图片后开始检索",
                disabled: !queryImage.value,
                onClick: startSearch
              }, " 开 始 搜 索 ", 8, _hoisted_11)
            ])
          ]),
          createBaseVNode("section", _hoisted_12, [
            createBaseVNode("div", _hoisted_13, [
              galleryImages.value.length ? (openBlock(), createElementBlock("span", _hoisted_14, " 共 " + toDisplayString(galleryImages.value.length) + " 张 ", 1)) : createCommentVNode("", true),
              galleryLoading.value ? (openBlock(), createElementBlock("div", _hoisted_15, [..._cache[4] || (_cache[4] = [
                createBaseVNode("span", {
                  class: "spinner",
                  "aria-hidden": "true"
                }, null, -1),
                createBaseVNode("p", null, "正在扫描目录…", -1)
              ])])) : galleryError.value ? (openBlock(), createElementBlock("div", _hoisted_16, toDisplayString(galleryError.value), 1)) : galleryImages.value.length ? (openBlock(), createElementBlock("div", _hoisted_17, [
                (openBlock(true), createElementBlock(Fragment, null, renderList(galleryImages.value, (item) => {
                  return openBlock(), createElementBlock("figure", {
                    key: item.url,
                    class: "result-item"
                  }, [
                    createBaseVNode("img", {
                      src: item.url,
                      alt: item.name,
                      title: item.name,
                      loading: "lazy"
                    }, null, 8, _hoisted_18),
                    createBaseVNode("figcaption", null, toDisplayString(item.name), 1)
                  ]);
                }), 128))
              ])) : (openBlock(), createElementBlock("div", _hoisted_19, [..._cache[5] || (_cache[5] = [
                createBaseVNode("svg", {
                  class: "card-empty__icon",
                  viewBox: "0 0 48 48",
                  fill: "none",
                  "aria-hidden": "true"
                }, [
                  createBaseVNode("path", {
                    d: "M6 14a4 4 0 0 1 4-4h8l4 5h16a4 4 0 0 1 4 4v17a4 4 0 0 1-4 4H10a4 4 0 0 1-4-4V14z",
                    stroke: "currentColor",
                    "stroke-width": "2.6",
                    "stroke-linejoin": "round"
                  }),
                  createBaseVNode("path", {
                    d: "M18 27l6-6 5 5 3-3 6 6",
                    stroke: "currentColor",
                    "stroke-width": "2.6",
                    "stroke-linecap": "round",
                    "stroke-linejoin": "round"
                  })
                ], -1),
                createBaseVNode("p", null, [
                  createTextVNode("点击右下角「目录」"),
                  createBaseVNode("br"),
                  createTextVNode("加载本地图片库")
                ], -1)
              ])]))
            ]),
            createBaseVNode("div", _hoisted_20, [
              createBaseVNode("div", {
                class: "dir-display",
                title: galleryFolder.value
              }, [
                createBaseVNode("span", _hoisted_22, toDisplayString(galleryFolder.value || "未选择目录"), 1)
              ], 8, _hoisted_21),
              createBaseVNode("button", {
                class: "dir-group__btn",
                type: "button",
                onClick: selectDirectory
              }, "目 录")
            ])
          ])
        ]),
        (openBlock(), createBlock(Teleport, { to: "body" }, [
          createVNode(Transition, { name: "toast-fade" }, {
            default: withCtx(() => [
              toastVisible.value ? (openBlock(), createElementBlock("div", _hoisted_23, toDisplayString(toastMessage.value), 1)) : createCommentVNode("", true)
            ]),
            _: 1
          })
        ])),
        (openBlock(), createBlock(Teleport, { to: "body" }, [
          ctxMenu.value.visible ? (openBlock(), createElementBlock("div", {
            key: 0,
            class: "ctx-overlay",
            onClick: closeCtxMenu,
            onContextmenu: withModifiers(closeCtxMenu, ["prevent"])
          }, [
            createBaseVNode("div", {
              class: "ctx-menu",
              style: normalizeStyle({ left: `${ctxMenu.value.x}px`, top: `${ctxMenu.value.y}px` })
            }, [
              createBaseVNode("button", {
                class: "ctx-menu__item",
                type: "button",
                onClick: ctxZoom
              }, "放 大"),
              createBaseVNode("button", {
                class: "ctx-menu__item",
                type: "button",
                onClick: ctxCopyPath
              }, "复制路径"),
              createBaseVNode("button", {
                class: "ctx-menu__item",
                type: "button",
                onClick: ctxDownload
              }, "下 载")
            ], 4)
          ], 32)) : createCommentVNode("", true)
        ])),
        (openBlock(), createBlock(Teleport, { to: "body" }, [
          createVNode(Transition, { name: "view-fade" }, {
            default: withCtx(() => [
              lightboxVisible.value ? (openBlock(), createElementBlock("div", {
                key: 0,
                class: "lightbox",
                onClick: _cache[0] || (_cache[0] = ($event) => lightboxVisible.value = false)
              }, [
                createBaseVNode("img", {
                  src: queryImage.value?.url,
                  alt: queryImage.value?.name
                }, null, 8, _hoisted_24)
              ])) : createCommentVNode("", true)
            ]),
            _: 1
          })
        ]))
      ]);
    };
  }
};
const SearchView = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-976ab3d0"]]);
export {
  SearchView as default
};
