library(dplyr)
library(ggplot2)
library(tidyr)
library(readr)
library("RColorBrewer")
args = commandArgs(TRUE)

load_data <- function(directory){
  wd = getwd()
  setwd(directory)
  data <- readr::read_csv("output.csv")
  return(data)
}

filter_data <- function(data, percent=0.5){
  return(
    data %>% group_by(weight, dataset, label) %>%
      arrange(confidence) %>%
      filter(confidence >= quantile(confidence, percent)) %>%
      ungroup()
  )
}

plot_data <- function(data, percent=0.7){
  

  
  data <- data %>% mutate(Correct_Classifications=correct_classifications/total_classifications)
  data <- data %>% mutate(Intersection_Over_Union=average_iou)
  
  #d = data %>% gather(Dataset, IoU, dataset:Intersection_Over_Union)
  
  data = data %>% filter_data(percent)
  
  pearson = cor(method="pearson", data$average_iou, data$confidence)
  
  # p = data %>% 
  #   ggplot(aes(x=as.factor(weight), y=Value, color=dataset, fill=dataset, group=interaction(dataset, weight))) +
  #   geom_boxplot() +
  #   #scale_x_log10() +
  #   xlab("Training Iterations") +    
  #   ylab("Observation") +
  #   scale_x_discrete() +
  #   scale_y_log10() +
  #   theme_minimal() +
  #   theme(axis.text.x = element_text(angle = 45, hjust = 1))
  
  
  p = data %>%
    ggplot(aes(x=weight, y=Intersection_Over_Union, color=dataset, fill=dataset)) +
    geom_point(alpha=0.05) +
    geom_smooth(method="loess", se=F) +
    #geom_smooth(method="lm", se=F) +
    #scale_x_log10() +
    labs(x="Training Iteration",
           y="Intersection Over Union",
         title=paste("IoU for grayscale images with confidence in top", (100*(1-percent)), "quantile")) +
    #scale_x_discrete() +
    #scale_y_log10() +
    theme_minimal() +
    #facet_wrap(~dataset, scales = "free") +
    ylim(0.0, 1.0) +
    theme(axis.text.x = element_text(angle = 45, hjust = 1))+
    scale_fill_brewer(palette="Set1") + 
    scale_color_brewer(palette="Set1")
    


  
  # p <- d %>% 
  #   filter(Observation == "Intersection_Over_Union") %>%
  #   ggplot(aes(x=weight, y=Value, fill=Observation)) +
  #   geom_point() +
  #   geom_smooth()
  
  # p = data %>%
  #   ggplot(aes(x=confidence, y=Correct_Classifications)) +
  #   geom_point() +
  #   scale_x_log10() +
  #   ylab("Correctness") +
  #   xlab("Confidence")
  # # 
  # totals = data %>%
  #   group_by(label, weight) %>%
  #   summarise(total = sum(total_classifications))
  # 
  # p = totals %>%
  #   ggplot(aes(x=label, y=total, fill=label, group=label)) +
  #   geom_bar(stat="identity") +
  #   scale_y_log10() +
  #   facet_wrap(~weight) +
  #   theme(axis.text.x = element_blank(),
  #         axis.ticks.x = element_blank())
  
  print(p)
  
  return()
}

run_script <- function(directory, percent=0.7){
  d = load_data(directory)
  plot_data(d, percent)
}